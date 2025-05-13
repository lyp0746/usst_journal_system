from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View

from .models import SystemSetting, SystemLog
from .forms import SystemSettingForm, ResearchFieldForm, UserEditForm
from accounts.models import User, ResearchField, UserRole
from manuscripts.models import Manuscript
from django.db.models import Count

@login_required
def dashboard(request):
    if not request.user.is_superuser and 'Admin' not in request.user.roles.values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")
    context = {
        'user_count': User.objects.count(),
        'manuscript_count': Manuscript.objects.count(),
        'published_count': Manuscript.objects.filter(status='PUBLISHED').count(),
    }
    return render(request, 'admin_management/dashboard.html', context)

@login_required
def settings(request):
    if not request.user.is_superuser and 'Admin' not in request.user.roles.values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")
    settings_list = SystemSetting.objects.all()
    form = SystemSettingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "设置保存成功")
        return redirect('admin_settings')
    return render(request, 'admin_management/settings.html', {'settings_list': settings_list, 'form': form})

@login_required
def research_fields(request):
    if not request.user.is_superuser and 'Admin' not in request.user.roles.values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")
    fields = ResearchField.objects.all()
    form = ResearchFieldForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "研究领域保存成功")
        return redirect('research_fields')
    return render(request, 'admin_management/research_fields.html', {'fields': fields, 'form': form})


from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
import os
import zipfile
from datetime import datetime


@login_required
def error_logs(request):
    if not request.user.is_superuser and 'Admin' not in request.user.roles.values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")
    logs = SystemLog.objects.filter(is_error=True).order_by('-timestamp')
    return render(request, 'admin_management/error_logs.html', {'logs': logs})


@login_required
def backup(request):
    if not request.user.is_superuser and 'Admin' not in request.user.roles.values_list('role__name', flat=True):
        return HttpResponseForbidden("无权限访问")
    if request.method == 'POST':
        backup_dir = 'media/backups'
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_path = f'{backup_dir}/backup_{timestamp}.zip'

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write('media/db.sqlite3', 'db.sqlite3')
            for root, _, files in os.walk('media'):
                for file in files:
                    if file != 'db.sqlite3' and not file.startswith('backup_'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, 'media')
                        zipf.write(file_path, f'media/{arcname}')

        response = FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=f'backup_{timestamp}.zip')
        return response
    return render(request, 'admin_management/backup.html')


class UserAuditView(View):
    template_name = 'admin_management/user_audit.html'

    def get(self, request):
        pending_users = UserRole.objects.filter(is_active=False, role__name='Reviewer')
        return render(request, self.template_name, {'pending_users': pending_users})

    def post(self, request):
        user_role_id = request.POST.get('user_role_id')
        action = request.POST.get('action')
        user_role = UserRole.objects.get(id=user_role_id)
        if action == 'approve':
            user_role.is_active = True
            user_role.save()
            SystemLog.objects.create(
                user=request.user, action=f"批准审稿人 {user_role.user.username}", details="用户角色激活"
            )
            messages.success(request, f"已批准 {user_role.user.username} 的审稿人角色")
        elif action == 'reject':
            reason = request.POST.get('reason')
            SystemLog.objects.create(
                user=request.user, action=f"拒绝审稿人 {user_role.user.username}",
                details=f"原因: {reason}"
            )
            user_role.delete()
            messages.success(request, f"已拒绝 {user_role.user.username} 的审稿人角色")
        return redirect('user_audit')

class UserManagementView(View):
    template_name = 'admin_management/user_management.html'

    def get(self, request):
        users = User.objects.all()
        return render(request, self.template_name, {'users': users})

    def post(self, request):
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = User.objects.get(id=user_id)
        if action == 'disable':
            user.is_active = False
            user.save()
            SystemLog.objects.create(
                user=request.user, action=f"禁用用户 {user.username}", details="用户账号禁用"
            )
            messages.success(request, f"已禁用 {user.username} 的账号")
        return redirect('user_management')

class UserEditView(View):
    template_name = 'admin_management/user_edit.html'

    def get(self, request, user_id):
        user = User.objects.get(id=user_id)
        form = UserEditForm(instance=user)
        return render(request, self.template_name, {'form': form, 'user': user})

    def post(self, request, user_id):
        user = User.objects.get(id=user_id)
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            SystemLog.objects.create(
                user=request.user, action=f"编辑用户 {user.username}", details="用户信息更新"
            )
            messages.success(request, f"已更新 {user.username} 的信息")
            return redirect('user_management')
        return render(request, self.template_name, {'form': form, 'user': user})