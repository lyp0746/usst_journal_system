from django.db import models
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Notification
from .forms import NotificationSearchForm


@login_required
def notification_list(request):
    # 清理无效参数
    if any(key == '=' or not key for key in request.GET):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(request.path)

    # 创建表单实例，确保使用request.GET
    form = NotificationSearchForm(request.GET or None)

    # 初始查询集
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    # 应用过滤条件
    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        notification_type = form.cleaned_data.get('notification_type')
        is_read_str = form.cleaned_data.get('is_read')

        if keyword:
            notifications = notifications.filter(
                models.Q(title__icontains=keyword) |
                models.Q(message__icontains=keyword)
            )

        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)

        if is_read_str:
            is_read_bool = is_read_str == 'True'
            notifications = notifications.filter(is_read=is_read_bool)

    # 分页处理
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except Exception:
        page_obj = paginator.page(1)

    return render(request, 'notifications/list.html', {
        'form': form,
        'page_obj': page_obj,
        'param_name': 'page',  # 重要！为分页模板提供param_name
    })


@login_required
def mark_read(request):
    if request.method == 'POST':
        notification_ids = request.POST.getlist('notification_ids')
        if not notification_ids:
            return JsonResponse({'success': False, 'error': '未选择任何通知'})

        try:
            # 打印调试信息
            print(f"标记已读: {notification_ids}")

            updated_count = Notification.objects.filter(
                id__in=notification_ids,
                recipient=request.user
            ).update(is_read=True)

            return JsonResponse({
                'success': True,
                'message': f'已将{updated_count}条通知标记为已读',
                'updated_ids': notification_ids
            })
        except Exception as e:
            print(f"标记已读错误: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '无效请求'})