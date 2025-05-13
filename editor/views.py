# editor/views.py
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from admin_management.models import SystemLog
from manuscripts.models import Manuscript
from accounts.models import ResearchField, UserRole
from notifications.models import Notification
from django.utils import timezone
from django.http import HttpResponseForbidden
from review_process.reviewer_matcher import match_reviewers


@login_required
def editor_dashboard(request):
    if 'Editor' not in UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")

    # 获取当前激活的标签页参数
    active_tab = request.GET.get('active_tab', 'new')

    # 基础查询集 - 可以选择只查看分配给自己的稿件或全部稿件
    show_mine_only = request.GET.get('show_mine_only', False)
    if show_mine_only:
        base_queryset = Manuscript.objects.filter(handling_editor=request.user)
    else:
        base_queryset = Manuscript.objects.all()

    # 应用过滤条件
    status = request.GET.get('status')
    field = request.GET.get('research_field')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 构建查询集
    filtered_queryset = base_queryset

    if status:
        filtered_queryset = filtered_queryset.filter(status=status)
    if field:
        filtered_queryset = filtered_queryset.filter(research_field__code=field)
    if start_date:
        filtered_queryset = filtered_queryset.filter(submit_date__gte=start_date)
    if end_date:
        filtered_queryset = filtered_queryset.filter(submit_date__lte=end_date)

    # 如果没有应用过滤，则按原来的方式分类展示
    if not any([status, field, start_date, end_date]):
        new_manuscripts = base_queryset.filter(status='SUBMITTED').order_by('-submit_date')
        under_review = base_queryset.filter(status='UNDER_REVIEW').order_by('-submit_date')
        pending_decision = base_queryset.filter(status__in=['REVISION_REQUIRED', 'REVISED']).order_by('-submit_date')

        # 分页处理
        new_paginator = Paginator(new_manuscripts, 5)
        review_paginator = Paginator(under_review, 5)
        decision_paginator = Paginator(pending_decision, 5)

        new_page = request.GET.get('new_page')
        review_page = request.GET.get('review_page')
        decision_page = request.GET.get('decision_page')

        new_page_obj = new_paginator.get_page(new_page)
        review_page_obj = review_paginator.get_page(review_page)
        decision_page_obj = decision_paginator.get_page(decision_page)

        context = {
            'new_page_obj': new_page_obj,
            'review_page_obj': review_page_obj,
            'decision_page_obj': decision_page_obj,
            'filtered_view': False,
            'active_tab': active_tab  # 添加激活标签页参数
        }
    else:
        # 如果有过滤条件，则直接分页展示过滤后的结果
        filtered_queryset = filtered_queryset.order_by('-submit_date')
        paginator = Paginator(filtered_queryset, 20)
        page = request.GET.get('page')
        manuscripts = paginator.get_page(page)

        context = {
            'manuscripts': manuscripts,
            'filtered_view': True,
            'applied_filters': {
                'status': status,
                'research_field': field,
                'start_date': start_date,
                'end_date': end_date,
                'show_mine_only': show_mine_only
            }
        }

    # 添加通用上下文数据
    research_fields = ResearchField.objects.filter(is_active=True)
    context.update({
        'research_fields': research_fields,
        'status_choices': Manuscript.STATUS_CHOICES
    })

    return render(request, 'editor/dashboard.html', context)

from .forms import InitialReviewForm
from manuscripts.models import Manuscript

@login_required
def initial_review(request, manuscript_id):
    manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id, status='SUBMITTED')
    if 'Editor' not in UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")

    if request.method == 'POST':
        form = InitialReviewForm(request.POST, instance=manuscript)
        if form.is_valid():
            manuscript = form.save(commit=False)
            manuscript.handling_editor = request.user
            manuscript.decision_date = timezone.now()
            manuscript.save()

            notification_type = 'DECISION' if manuscript.status == 'REJECT_INITIAL' else 'SUBMISSION'
            Notification.objects.create(
                recipient=manuscript.submitter,
                notification_type=notification_type,
                title=f"稿件 {manuscript.manuscript_id} 初审{'拒绝' if manuscript.status == 'REJECT_INITIAL' else '通过'}",
                message=f"您的稿件《{manuscript.title_cn}》{'初审未通过，原因：' + form.cleaned_data['comment'] if manuscript.status == 'REJECT_INITIAL' else '已通过初审，进入外审阶段'}",
                url=f"/manuscripts/detail/{manuscript.manuscript_id}/",
                related_id=manuscript.manuscript_id
            )
            with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                f.write(f"{timezone.now()}: 稿件 {manuscript.manuscript_id} 初审 {manuscript.status} by {request.user.username}\n")
            messages.success(request, "初审完成")
            return redirect('editor_dashboard')
    else:
        form = InitialReviewForm(instance=manuscript)
    return render(request, 'editor/initial_review.html', {'form': form, 'manuscript': manuscript})

from .forms import ReviewerAssignmentForm
from review_process.models import ReviewAssignment


@login_required
def assign_reviewer(request, manuscript_id):
    manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id, status='UNDER_REVIEW')
    if 'Editor' not in UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")

    recommended_reviewers = match_reviewers(manuscript, num_reviewers=5)
    if request.method == 'POST':
        form = ReviewerAssignmentForm(request.POST)
        if form.is_valid():
            for reviewer in form.cleaned_data['reviewers']:
                # 新增：防止重复分配审稿人
                reviewer_user = reviewer.user if hasattr(reviewer, 'user') else reviewer
                if ReviewAssignment.objects.filter(
                        manuscript=manuscript, reviewer=reviewer_user
                ).exists():
                    continue

                    # 创建审稿分配
                assignment = ReviewAssignment.objects.create(
                    manuscript=manuscript,
                    reviewer=reviewer_user,
                    assigned_by=request.user,
                    due_date=timezone.now() + timezone.timedelta(days=14)
                )

                # 创建通知
                Notification.objects.create(
                    recipient=reviewer_user,
                    notification_type='REVIEW_INVITE',
                    title=f"审稿邀请 {manuscript.manuscript_id}",
                    message=f"您被邀请审稿《{manuscript.title_cn}》，请在{14}天内响应",
                    url=f"/review_process/invitation/{manuscript.manuscript_id}/respond/",
                    related_id=manuscript.manuscript_id
                )

                # 记录文件日志
                with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                    f.write(
                        f"{timezone.now()}: 稿件 {manuscript.manuscript_id} 分配审稿人 by {request.user.username}\n")

                    # 新增：记录系统日志
                try:
                    SystemLog.objects.create(
                        user=request.user,
                        action='分配审稿人',
                        details=f'为稿件 {manuscript.manuscript_id} 分配审稿人 {reviewer_user.username}'
                    )
                except:
                    pass  # 如果SystemLog不存在，跳过此步骤

            messages.success(request, "审稿人分配成功")
            return redirect('editor_dashboard')
    else:
        form = ReviewerAssignmentForm()
        form.fields['reviewers'].queryset = UserRole.objects.filter(
            role__name='Reviewer', is_active=True, user__in=[r for r in recommended_reviewers]
        )
    return render(request, 'editor/assign_reviewer.html', {
        'form': form,
        'manuscript': manuscript,
        'recommended_reviewers': recommended_reviewers,
    })

from review_process.models import ReviewAssignment


@login_required
def progress_monitor(request, manuscript_id):
    manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id, status='UNDER_REVIEW')
    if 'Editor' not in UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")

    assignments = ReviewAssignment.objects.filter(manuscript=manuscript)

    # 构建时间线事件列表 - 使用正确的字段名
    timeline_events = []
    for assignment in assignments:
        # 添加邀请事件
        timeline_events.append({
            'date': assignment.invited_date,
            'description': f"{assignment.reviewer.username} 被邀请审稿"
        })

        # 添加响应事件
        if assignment.response_date:
            if assignment.status == 'ACCEPTED':
                timeline_events.append({
                    'date': assignment.response_date,
                    'description': f"{assignment.reviewer.username} 接受了审稿邀请"
                })
            elif assignment.status == 'DECLINED':
                timeline_events.append({
                    'date': assignment.response_date,
                    'description': f"{assignment.reviewer.username} 拒绝了审稿邀请"
                })

        # 添加完成事件 - 使用正确的字段名 completion_date
        if assignment.completion_date:
            timeline_events.append({
                'date': assignment.completion_date,
                'description': f"{assignment.reviewer.username} 完成了审稿"
            })

    # 按日期排序
    timeline_events.sort(key=lambda x: x['date'])

    # 审稿提醒和通知逻辑
    for assignment in assignments:
        if assignment.status == 'INVITED' and assignment.invited_date < timezone.now() - timezone.timedelta(days=3):
            Notification.objects.create(
                recipient=assignment.reviewer,
                notification_type='REVIEW_REMINDER',
                title=f"审稿邀请 {manuscript.manuscript_id} 提醒",
                message=f"您尚未响应稿件《{manuscript.title_cn}》的审稿邀请，请尽快处理",
                url=f"/review_process/invitation/{assignment.id}/respond/",
                related_id=manuscript.manuscript_id
            )
            with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                f.write(f"{timezone.now()}: 审稿提醒 {manuscript.manuscript_id} to {assignment.reviewer.username}\n")
        elif assignment.status in ['ACCEPTED',
                                   'IN_PROGRESS'] and assignment.due_date < timezone.now() + timezone.timedelta(days=7):
            Notification.objects.create(
                recipient=assignment.reviewer,
                notification_type='REVIEW_REMINDER',
                title=f"审稿任务 {manuscript.manuscript_id} 提醒",
                message=f"稿件《{manuscript.title_cn}》的审稿截止日期为{assignment.due_date}，请按时完成",
                url=f"/review_process/review/{assignment.id}/form/",
                related_id=manuscript.manuscript_id
            )
            with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                f.write(
                    f"{timezone.now()}: 审稿截止提醒 {manuscript.manuscript_id} to {assignment.reviewer.username}\n")

    return render(request, 'editor/progress_monitor.html', {
        'manuscript': manuscript,
        'assignments': assignments,
        'timeline_events': timeline_events
    })

@login_required
def replace_reviewer(request, assignment_id):
    assignment = get_object_or_404(ReviewAssignment, id=assignment_id, status__in=['INVITED', 'DECLINED'])
    if 'Editor' not in UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")

    manuscript = assignment.manuscript
    recommended_reviewers = match_reviewers(manuscript, num_reviewers=5)
    if request.method == 'POST':
        new_reviewer_id = request.POST.get('new_reviewer')
        new_reviewer = get_object_or_404(User, id=new_reviewer_id)
        assignment.reviewer = new_reviewer
        assignment.status = 'INVITED'
        assignment.invited_date = timezone.now()
        assignment.due_date = timezone.now() + timezone.timedelta(days=14)
        assignment.decline_reason = ''
        assignment.save()

        Notification.objects.create(
            recipient=new_reviewer,
            notification_type='REVIEW_INVITE',
            title=f"审稿邀请 {manuscript.manuscript_id}",
            message=f"您被邀请审稿《{manuscript.title_cn}》，请在{14}天内响应",
            url=f"/review_process/invitation/{assignment.id}/respond/",
            related_id=manuscript.manuscript_id
        )
        with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timezone.now()}: 审稿人替换 {manuscript.manuscript_id} to {new_reviewer.username}\n")
        messages.success(request, "审稿人替换成功")
        return redirect('progress_monitor', manuscript_id=manuscript.manuscript_id)
    return render(request, 'editor/assign_reviewer.html', {
        'manuscript': manuscript,
        'recommended_reviewers': recommended_reviewers,
        'assignment': assignment,
    })

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from cairosvg import svg2png
from django.http import HttpResponse
from io import BytesIO

@login_required
def review_summary(request, manuscript_id):
    manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id, status__in=['UNDER_REVIEW', 'REVISION_REQUIRED', 'REVISED'])
    if 'Editor' not in UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")

    assignments = ReviewAssignment.objects.filter(manuscript=manuscript, status='COMPLETED')
    if request.GET.get('download') == 'pdf':
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.setFont("Helvetica", 12)
        p.drawString(100, 800, f"审稿意见汇总 - {manuscript.manuscript_id}")
        y = 750
        for assignment in assignments:
            review = assignment.review_form
            p.drawString(100, y, f"审稿人: {assignment.reviewer.username}")
            p.drawString(100, y-20, f"原创性: {review.originality_score}/5")
            p.drawString(100, y-40, f"技术水平: {review.technical_score}/5")
            p.drawString(100, y-60, f"表达: {review.presentation_score}/5")
            p.drawString(100, y-80, f"建议: {review.get_decision_display()}")
            p.drawString(100, y-100, f"给作者的评语: {review.comments_to_author[:100]}...")
            y -= 120
        p.showPage()
        p.save()
        buffer.seek(0)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="review_summary_{manuscript.manuscript_id}.pdf"'
        response.write(buffer.getvalue())
        return response
    return render(request, 'editor/review_summary.html', {'manuscript': manuscript, 'assignments': assignments})

from .forms import DecisionForm

@login_required
def decision_form(request, manuscript_id):
    manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id, status__in=['UNDER_REVIEW', 'REVISION_REQUIRED', 'REVISED'])
    if 'Editor' not in UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")

    if request.method == 'POST':
        form = DecisionForm(request.POST, instance=manuscript)
        if form.is_valid():
            manuscript = form.save(commit=False)
            manuscript.decision_date = timezone.now()
            manuscript.save()

            notification_type = {
                'ACCEPTED': 'ACCEPT',
                'REVISION_REQUIRED': 'REVISION',
                'REJECTED': 'REJECT'
            }[manuscript.status]
            Notification.objects.create(
                recipient=manuscript.submitter,
                notification_type=notification_type,
                title=f"稿件 {manuscript.manuscript_id} 编辑决定",
                message=f"您的稿件《{manuscript.title_cn}》已被{manuscript.get_status_display()}，编辑意见：{form.cleaned_data['decision_comment']}",
                url=f"/manuscripts/detail/{manuscript.manuscript_id}/",
                related_id=manuscript.manuscript_id
            )
            with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                f.write(f"{timezone.now()}: 稿件 {manuscript.manuscript_id} 决定 {manuscript.status} by {request.user.username}\n")
            messages.success(request, "编辑决定已提交")
            return redirect('editor_dashboard')
    else:
        form = DecisionForm(instance=manuscript)
    return render(request, 'editor/decision_form.html', {'form': form, 'manuscript': manuscript})