from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Volume, Issue, ManuscriptPublication
from .forms import VolumeForm, IssueForm, ManuscriptPublicationForm
from manuscripts.models import Manuscript
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.urls import reverse
from notifications.models import Notification
from datetime import datetime
import cairosvg

@login_required
def volume_list(request):
    volumes = Volume.objects.all()
    form = VolumeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "卷创建成功")
        return redirect('volume_list')
    return render(request, 'publication/volume_list.html', {'volumes': volumes, 'form': form})

@login_required
def issue_create(request, volume_id):
    volume = get_object_or_404(Volume, id=volume_id)
    form = IssueForm(request.POST or None, initial={'volume': volume})
    if request.method == 'POST' and form.is_valid():
        issue = form.save()
        messages.success(request, "期创建成功")
        return redirect('volume_list')
    return render(request, 'publication/issue_create.html', {'form': form, 'volume': volume})

@login_required
def arrange_manuscripts(request, volume_id, issue_id):
    issue = get_object_or_404(Issue, volume_id=volume_id, issue_number=issue_id)
    form = ManuscriptPublicationForm(request.POST or None, initial={'issue': issue})
    if request.method == 'POST' and form.is_valid():
        publication = form.save(commit=False)
        publication.doi = f"10.1000/MS{publication.manuscript.manuscript_id}"  # 模拟DOI
        publication.save()
        manuscript = publication.manuscript
        manuscript.status = 'PUBLISHED'
        manuscript.volume = volume_id
        manuscript.issue = issue_id
        manuscript.publish_date = publication.publication_date
        manuscript.save()
        Notification.objects.create(
            recipient=manuscript.submitter,
            notification_type='PUBLICATION',
            title=f"稿件 {manuscript.manuscript_id} 已出版",
            message=f"您的稿件已安排在卷 {volume_id} 期 {issue_id}，DOI: {publication.doi}",
            url=reverse('manuscript_detail', args=[manuscript.manuscript_id])
        )
        messages.success(request, "稿件安排成功")
        return redirect('arrange_manuscripts', volume_id=volume_id, issue_id=issue_id)
    publications = ManuscriptPublication.objects.filter(issue=issue)
    return render(request, 'publication/arrange_manuscripts.html', {'form': form, 'issue': issue, 'publications': publications})

@login_required
def generate_toc(request, volume_id, issue_id):
    issue = get_object_or_404(Issue, volume_id=volume_id, issue_number=issue_id)
    publications = ManuscriptPublication.objects.filter(issue=issue)
    if request.method == 'POST':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="TOC_V{volume_id}_I{issue_id}.pdf"'
        p = canvas.Canvas(response, pagesize=A4)
        p.setFont("Helvetica", 12)
        p.drawString(100, 800, f"《上海理工大学学报》 卷 {volume_id} 期 {issue_id} 目录")
        y = 750
        for pub in publications:
            p.drawString(100, y, f"{pub.manuscript.title_cn} - {pub.manuscript.authors} ({pub.page_start}-{pub.page_end})")
            y -= 20
        p.showPage()
        p.save()
        issue.is_published = True
        issue.save()
        volume = issue.volume
        volume.is_published = True
        volume.save()
        messages.success(request, "目录生成并发布成功")
        return response
    return render(request, 'publication/generate_toc.html', {'issue': issue, 'publications': publications})