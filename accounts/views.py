# accounts/views.py
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from manuscripts.models import Manuscript
from publication.models import Issue
from review_process.models import ReviewAssignment
from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserRole, UserProfile


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                institution=form.cleaned_data['institution'],
                title=form.cleaned_data['title'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                orcid=form.cleaned_data['orcid']
            )
            user.profile.research_fields.set(form.cleaned_data['research_fields'])
            UserRole.objects.create(user=user, role_id=1)  # 默认分配投稿人角色
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=request.user.profile)
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def dashboard(request):
    user_roles = UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True)
    context = {
        'user_roles': user_roles,
        'manuscripts': Manuscript.objects.filter(submitter=request.user) if 'Author' in user_roles else [],
        'review_assignments': ReviewAssignment.objects.filter(reviewer=request.user) if 'Reviewer' in user_roles else [],
        'editor_manuscripts': Manuscript.objects.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']) if 'Editor' in user_roles else [],
        'editor_issues': Issue.objects.all() if 'Editor' in user_roles else [],
        'user_count': User.objects.count() if request.user.is_superuser or 'Admin' in user_roles else 0,
        'manuscript_count': Manuscript.objects.count() if request.user.is_superuser or 'Admin' in user_roles else 0,
        'published_count': Manuscript.objects.filter(status='PUBLISHED').count() if request.user.is_superuser or 'Admin' in user_roles else 0,
    }
    return render(request, 'accounts/dashboard.html', context)