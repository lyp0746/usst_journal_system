# manuscripts/views.py
from django.db import models
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.views import View

from accounts.models import ResearchField, UserProfile
from .models import Manuscript, ManuscriptType
from .forms import ManuscriptSubmissionForm, ManuscriptRevisionForm, ManuscriptSearchForm
from notifications.models import Notification
from django.urls import reverse
import os


@login_required
def submission(request):
    # 确保用户资料已经创建
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        # 如果用户没有资料，创建一个空的资料
        messages.warning(request, "请先完善您的个人资料")
        return redirect('edit_profile')

    if request.method == 'POST':
        form = ManuscriptSubmissionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            manuscript = form.save(user=request.user)

            # 如果是正式提交，创建通知
            if manuscript.status == 'SUBMITTED':
                Notification.objects.create(
                    recipient=request.user,
                    notification_type='SUBMISSION',
                    title=f"稿件 {manuscript.manuscript_id} 已提交",
                    message=f"您的稿件《{manuscript.title_cn}》已成功提交，查重率：{manuscript.similarity_rate:.2f}%",
                    url=reverse('manuscript_detail', args=[manuscript.manuscript_id]),
                    related_id=manuscript.manuscript_id
                )
                with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{timezone.now()}: 稿件 {manuscript.manuscript_id} 提交 by {request.user.username}\n")

            messages.success(request, "稿件已保存" if manuscript.status == 'DRAFT' else "稿件已提交")
            return redirect('manuscript_list')
    else:
        form = ManuscriptSubmissionForm(user=request.user)

    return render(request, 'manuscripts/submission.html', {'form': form})

@login_required
def manuscript_list(request):
    form = ManuscriptSearchForm(request.GET or None)
    manuscripts = Manuscript.objects.filter(submitter=request.user).order_by('-created_at')

    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        status = form.cleaned_data.get('status')
        research_field = form.cleaned_data.get('research_field')

        if keyword:
            manuscripts = manuscripts.filter(
                models.Q(title_cn__icontains=keyword) |
                models.Q(title_en__icontains=keyword) |
                models.Q(manuscript_id__icontains=keyword)
            )
        if status:
            manuscripts = manuscripts.filter(status=status)
        if research_field:
            manuscripts = manuscripts.filter(research_field=research_field)

            # 添加状态选项
    status_choices = Manuscript.STATUS_CHOICES

    # 获取研究领域
    research_fields = ResearchField.objects.filter(is_active=True)

    paginator = Paginator(manuscripts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'manuscripts/list.html', {
        'form': form,
        'page_obj': page_obj,
        'status_choices': status_choices,
        'research_fields': research_fields
    })

@login_required
def manuscript_detail(request, manuscript_id):
    manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id, submitter=request.user)
    return render(request, 'manuscripts/detail.html', {'manuscript': manuscript})

@login_required
def revise_manuscript(request, manuscript_id):
    manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id, submitter=request.user, status='REVISION_REQUIRED')
    if request.method == 'POST':
        form = ManuscriptRevisionForm(request.POST, request.FILES, instance=manuscript)
        if form.is_valid():
            manuscript = form.save(commit=False)
            manuscript.status = 'REVISED'
            manuscript.save()
            Notification.objects.create(
                recipient=request.user,
                notification_type='REVISION',
                title=f"稿件 {manuscript.manuscript_id} 已修改",
                message=f"您的稿件《{manuscript.title_cn}》已提交修改稿",
                url=reverse('manuscript_detail', args=[manuscript.manuscript_id]),
                related_id=manuscript.manuscript_id
            )
            with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
                f.write(f"{timezone.now()}: 稿件 {manuscript.manuscript_id} 修改 by {request.user.username}\n")
            messages.success(request, "修改稿已提交")
            return redirect('manuscript_list')
    else:
        form = ManuscriptRevisionForm(instance=manuscript)
    return render(request, 'manuscripts/revise.html', {'form': form, 'manuscript': manuscript})

@login_required
def withdraw_manuscript(request, manuscript_id):
    manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id, submitter=request.user)
    if manuscript.status in ['SUBMITTED', 'UNDER_REVIEW']:
        manuscript.status = 'REJECTED'
        manuscript.save()
        Notification.objects.create(
            recipient=request.user,
            notification_type='REJECT',
            title=f"稿件 {manuscript.manuscript_id} 已撤回",
            message=f"您的稿件《{manuscript.title_cn}》已撤回",
            url=reverse('manuscript_detail', args=[manuscript.manuscript_id]),
            related_id=manuscript.manuscript_id
        )
        with open('media/notifications/log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timezone.now()}: 稿件 {manuscript.manuscript_id} 撤回 by {request.user.username}\n")
        messages.success(request, "稿件已撤回")
    return redirect('manuscript_list')

def guidelines(request):
    return render(request, 'manuscripts/guidelines.html')

def download_template(request):
    template_path = 'media/template.docx'
    with open(template_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = 'attachment; filename=template.docx'
        return response

class ManuscriptFileDownloadView(View):
    def get(self, request, manuscript_id):
        manuscript = get_object_or_404(Manuscript, manuscript_id=manuscript_id)
        if not request.user == manuscript.submitter and not request.user.is_superuser:
            raise Http404("无权限访问")
        file_path = manuscript.manuscript_file.path
        file_name = manuscript.manuscript_file.name.split('/')[-1]
        response = FileResponse(open(file_path, 'rb'), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response