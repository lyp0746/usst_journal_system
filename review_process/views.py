# review_process/views.py
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import ReviewerProfile, ReviewAssignment, ReviewForm
from .forms import ReviewerProfileForm, ReviewInvitationResponseForm, ReviewFormForm
from notifications.models import Notification
from django.urls import reverse
from django.utils import timezone

@login_required
def reviewer_profile(request):
    profile, created = ReviewerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ReviewerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "资料更新成功")
            return redirect('reviewer_profile')
    else:
        form = ReviewerProfileForm(instance=profile)
    return render(request, 'review_process/reviewer_profile.html', {'form': form})

@login_required
def invitation_list(request):
    # 获取基础查询集
    assignments = ReviewAssignment.objects.filter(reviewer=request.user).order_by('-invited_date')

    # 处理状态筛选
    status_filter = request.GET.get('status')
    if status_filter:
        assignments = assignments.filter(status=status_filter)

    # 添加状态选项到上下文
    status_choices = ReviewAssignment.STATUS_CHOICES

    # 分页处理
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'review_process/invitation_list.html', {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'param_name': 'page'  # 添加param_name参数给分页模板
    })

@login_required
def respond_invitation(request, assignment_id):
    assignment = get_object_or_404(ReviewAssignment, id=assignment_id, reviewer=request.user, status='INVITED')
    if request.method == 'POST':
        form = ReviewInvitationResponseForm(request.POST)
        if form.is_valid():
            response = form.cleaned_data['response']
            assignment.response_date = timezone.now()
            if response == 'ACCEPT':
                assignment.status = 'ACCEPTED'
                assignment.due_date = timezone.now() + timezone.timedelta(days=14)
                Notification.objects.create(
                    recipient=request.user,
                    notification_type='REVIEW_INVITE',
                    title=f"审稿邀请 {assignment.manuscript.manuscript_id} 已接受",
                    message=f"您已接受稿件《{assignment.manuscript.title_cn}》的审稿邀请，截止日期：{assignment.due_date}",
                    url=reverse('manuscript_view', args=[assignment.manuscript.manuscript_id]),
                    related_id=assignment.manuscript.manuscript_id
                )
            else:
                assignment.status = 'DECLINED'
                assignment.decline_reason = form.cleaned_data['decline_reason']
                Notification.objects.create(
                    recipient=assignment.assigned_by,
                    notification_type='REVIEW_INVITE',
                    title=f"审稿邀请 {assignment.manuscript.manuscript_id} 被拒绝",
                    message=f"审稿人 {request.user.username} 拒绝了稿件《{assignment.manuscript.title_cn}》的审稿邀请，理由：{assignment.decline_reason}",
                    related_id=assignment.manuscript.manuscript_id
                )
            assignment.save()
            with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                f.write(f"{timezone.now()}: 审稿任务 {assignment.manuscript.manuscript_id} {assignment.status} by {request.user.username}\n")
            messages.success(request, "响应已提交")
            return redirect('invitation_list')
    else:
        form = ReviewInvitationResponseForm()
    return render(request, 'review_process/respond_invitation.html', {'form': form, 'assignment': assignment})

@login_required
def manuscript_view(request, manuscript_id):
    assignment = get_object_or_404(
        ReviewAssignment,
        manuscript__manuscript_id=manuscript_id,
        reviewer=request.user,
        status__in=['ACCEPTED', 'IN_PROGRESS', 'COMPLETED']
    )
    manuscript = assignment.manuscript
    return render(request, 'review_process/manuscript_view.html', {'manuscript': manuscript, 'assignment': assignment})

@login_required
def review_form(request, assignment_id):
    assignment = get_object_or_404(
        ReviewAssignment, id=assignment_id, reviewer=request.user, status__in=['ACCEPTED', 'IN_PROGRESS']
    )
    review_form, created = ReviewForm.objects.get_or_create(assignment=assignment)
    if request.method == 'POST':
        form = ReviewFormForm(request.POST, instance=review_form)
        if form.is_valid():
            review_form = form.save(commit=False)
            if 'submit' in request.POST:
                assignment.status = 'COMPLETED'
                assignment.completion_date = timezone.now()
                review_form.save()
                assignment.save()
                Notification.objects.create(
                    recipient=assignment.assigned_by,
                    notification_type='DECISION',
                    title=f"审稿 {assignment.manuscript.manuscript_id} 已完成",
                    message=f"审稿人 {request.user.username} 已完成稿件《{assignment.manuscript.title_cn}》的评审",
                    url=reverse('review_summary', args=[assignment.manuscript.manuscript_id]),
                    related_id=assignment.manuscript.manuscript_id
                )
                with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{timezone.now()}: 审稿 {assignment.manuscript.manuscript_id} 完成 by {request.user.username}\n")
                messages.success(request, "评审已提交")
                return redirect('invitation_list')
            else:
                assignment.status = 'IN_PROGRESS'
                review_form.save()
                assignment.save()
                messages.success(request, "草稿已保存")
    else:
        form = ReviewFormForm(instance=review_form)
    return render(request, 'review_process/review_form.html', {'form': form, 'assignment': assignment})


@login_required
def review_history(request):
    # 基础查询集：已完成的审稿任务
    assignments = ReviewAssignment.objects.filter(
        reviewer=request.user, status='COMPLETED'
    ).order_by('-completion_date')

    # 添加类视图中的关键词搜索功能
    keywords = request.GET.get('keywords')
    if keywords:
        assignments = assignments.filter(
            Q(manuscript__keywords_cn__icontains=keywords) |
            Q(manuscript__keywords_en__icontains=keywords)
        )

        # 分页处理
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 为了兼容类视图中使用的变量名，也提供 assignments 变量
    context = {
        'page_obj': page_obj,
        'assignments': page_obj,  # 兼容类视图模板
        'keywords': keywords  # 回显搜索关键词
    }

    return render(request, 'review_process/review_history.html', context)