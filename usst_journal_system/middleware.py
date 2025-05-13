# usst_journal_system/middleware.py
from django.http import HttpResponseForbidden
from accounts.models import UserRole

class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.role_permissions = {
            'manuscripts': ['Author'],
            'review_process': ['Reviewer', 'Editor'],
            'editor': ['Editor'],
            'publication': ['Editor'],
            'analytics': ['Editor', 'Admin'],
            'admin_management': ['Admin']
        }

    def __call__(self, request):
        if request.user.is_authenticated:
            user_roles = UserRole.objects.filter(user=request.user, is_active=True).values_list('role__name', flat=True)
            path = request.path
            for prefix, allowed_roles in self.role_permissions.items():
                if path.startswith(f'/{prefix}/') and not any(role in user_roles for role in allowed_roles) and not request.user.is_superuser:
                    return HttpResponseForbidden("无权限访问")
        return self.get_response(request)