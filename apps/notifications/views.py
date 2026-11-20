from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
import json

from apps.notifications.models import Notification, NotificationPreference
from apps.audit.models import ActivityLog


CATEGORY_TYPES = {
    'tasks': [
        'task_assigned', 'task_completed', 'task_overdue', 'task_submitted',
        'task_approved', 'changes_requested', 'deadline_approaching'
    ],
    'projects': [
        'project_update', 'file_shared', 'meeting_invite', 'overtime_request',
        'overtime_decision'
    ],
    'messages': [
        'new_message'
    ],
    'system': [
        'system', 'member_joined'
    ],
    'mentions': [
        'mention'
    ],
}

NOTIFICATION_META = {
    'task_assigned': {'icon': 'ri-file-text-line', 'color_class': 'icon-red', 'bg_color': '#fee2e2', 'icon_color': '#ef4444', 'category': 'tasks'},
    'task_completed': {'icon': 'ri-check-line', 'color_class': 'icon-green', 'bg_color': '#dcfce7', 'icon_color': '#22c55e', 'category': 'tasks'},
    'task_overdue': {'icon': 'ri-error-warning-line', 'color_class': 'icon-red', 'bg_color': '#fee2e2', 'icon_color': '#ef4444', 'category': 'tasks'},
    'task_submitted': {'icon': 'ri-file-upload-line', 'color_class': 'icon-orange', 'bg_color': '#ffedd5', 'icon_color': '#f97316', 'category': 'tasks'},
    'task_approved': {'icon': 'ri-shield-check-line', 'color_class': 'icon-green', 'bg_color': '#dcfce7', 'icon_color': '#16a34a', 'category': 'tasks'},
    'changes_requested': {'icon': 'ri-edit-line', 'color_class': 'icon-orange', 'bg_color': '#ffedd5', 'icon_color': '#ea580c', 'category': 'tasks'},
    'deadline_approaching': {'icon': 'ri-time-line', 'color_class': 'icon-orange', 'bg_color': '#ffedd5', 'icon_color': '#f59e0b', 'category': 'tasks'},
    'new_message': {'icon': 'ri-message-3-line', 'color_class': 'icon-blue', 'bg_color': '#dbeafe', 'icon_color': '#2563eb', 'category': 'messages'},
    'mention': {'icon': 'ri-at-line', 'color_class': 'icon-teal', 'bg_color': '#ccfbf1', 'icon_color': '#0d9488', 'category': 'mentions'},
    'project_update': {'icon': 'ri-group-line', 'color_class': 'icon-purple', 'bg_color': '#ede9fe', 'icon_color': '#7c3aed', 'category': 'projects'},
    'file_shared': {'icon': 'ri-file-line', 'color_class': 'icon-blue', 'bg_color': '#dbeafe', 'icon_color': '#2563eb', 'category': 'projects'},
    'meeting_invite': {'icon': 'ri-calendar-event-line', 'color_class': 'icon-purple', 'bg_color': '#ede9fe', 'icon_color': '#8b5cf6', 'category': 'projects'},
    'overtime_request': {'icon': 'ri-timer-line', 'color_class': 'icon-orange', 'bg_color': '#ffedd5', 'icon_color': '#d97706', 'category': 'projects'},
    'overtime_decision': {'icon': 'ri-check-double-line', 'color_class': 'icon-green', 'bg_color': '#dcfce7', 'icon_color': '#16a34a', 'category': 'projects'},
    'member_joined': {'icon': 'ri-user-add-line', 'color_class': 'icon-green', 'bg_color': '#dcfce7', 'icon_color': '#10b981', 'category': 'system'},
    'system': {'icon': 'ri-settings-4-line', 'color_class': 'icon-slate', 'bg_color': '#f1f5f9', 'icon_color': '#64748b', 'category': 'system'},
}


def format_time_ago(dt):
    if not dt:
        return ''
    now = timezone.now()
    diff = now - dt
    if diff.days == 0:
        return dt.strftime('%I:%M %p')
    elif diff.days == 1:
        return 'Yesterday'
    elif diff.days < 7:
        return dt.strftime('%a')
    else:
        return dt.strftime('%d %b %Y')


@login_required
def notification_list_view(request):
    all_notifications = request.user.notifications.all().select_related('actor').order_by('-created_at')

    # Counts
    total_count = all_notifications.count()
    unread_count = all_notifications.filter(is_read=False).count()
    tasks_count = all_notifications.filter(notification_type__in=CATEGORY_TYPES['tasks']).count()
    projects_count = all_notifications.filter(notification_type__in=CATEGORY_TYPES['projects']).count()
    messages_count = all_notifications.filter(notification_type__in=CATEGORY_TYPES['messages']).count()
    system_count = all_notifications.filter(notification_type__in=CATEGORY_TYPES['system']).count()
    mentions_count = all_notifications.filter(notification_type__in=CATEGORY_TYPES['mentions']).count()

    # Filter tab
    current_tab = request.GET.get('tab', 'all').lower()
    filtered_qs = all_notifications
    if current_tab in CATEGORY_TYPES:
        filtered_qs = filtered_qs.filter(notification_type__in=CATEGORY_TYPES[current_tab])

    # Search filter if provided
    query = request.GET.get('q', '').strip()
    if query:
        filtered_qs = filtered_qs.filter(title__icontains=query) | filtered_qs.filter(message__icontains=query)

    # Decorate notifications with metadata
    decorated_list = []
    for n in filtered_qs:
        meta = NOTIFICATION_META.get(n.notification_type, {
            'icon': 'ri-notification-3-line',
            'color_class': 'icon-blue',
            'bg_color': '#dbeafe',
            'icon_color': '#2563eb',
            'category': 'system'
        })
        decorated_list.append({
            'obj': n,
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at,
            'time_str': format_time_ago(n.created_at),
            'url': n.url or '#',
            'actor': n.actor,
            'type': n.notification_type,
            'category': meta['category'],
            'icon': meta['icon'],
            'bg_color': meta['bg_color'],
            'icon_color': meta['icon_color'],
        })

    # Pagination
    try:
        per_page = int(request.GET.get('per_page', 12))
    except (ValueError, TypeError):
        per_page = 12

    paginator = Paginator(decorated_list, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Recent activities from ActivityLog
    recent_logs = ActivityLog.objects.select_related('user').order_by('-timestamp')[:5]
    formatted_logs = []
    for l in recent_logs:
        avatar = l.user.profile_picture.url if l.user and l.user.profile_picture else ''
        name = l.user.get_full_name() or (l.user.email if l.user else 'System')
        initials = (l.user.first_name[:1] + l.user.last_name[:1]) if l.user and l.user.first_name else 'SY'
        formatted_logs.append({
            'user_name': name,
            'action': l.action,
            'details': l.details or f"{l.action} in {l.module}",
            'module': l.module,
            'time_str': format_time_ago(l.timestamp),
            'avatar': avatar,
            'initials': initials,
        })

    # Preferences
    pref, _ = NotificationPreference.objects.get_or_create(user=request.user)

    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
        'current_tab': current_tab,
        'query': query,
        'per_page': per_page,
        'total_count': total_count,
        'unread_count': unread_count,
        'tasks_count': tasks_count,
        'projects_count': projects_count,
        'messages_count': messages_count,
        'system_count': system_count,
        'mentions_count': mentions_count,
        'recent_logs': formatted_logs,
        'preferences': pref,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def mark_all_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'success': True, 'unread_count': 0})
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:list')


@login_required
def mark_notification_read_view(request, notification_id):
    n = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    n.mark_read()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        unread_cnt = request.user.notifications.filter(is_read=False).count()
        return JsonResponse({'success': True, 'unread_count': unread_cnt})
    if n.url and n.url != '#':
        return redirect(n.url)
    return redirect('notifications:list')


@login_required
def delete_notification_view(request, notification_id):
    n = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    n.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        unread_cnt = request.user.notifications.filter(is_read=False).count()
        total_cnt = request.user.notifications.count()
        return JsonResponse({'success': True, 'unread_count': unread_cnt, 'total_count': total_cnt})
    messages.success(request, 'Notification deleted.')
    return redirect('notifications:list')


@login_required
def bulk_action_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        ids = request.POST.getlist('notification_ids')

        # Check JSON payload if ajax
        if not ids and request.body:
            try:
                data = json.loads(request.body)
                action = data.get('action')
                ids = data.get('notification_ids', [])
            except Exception:
                pass

        qs = request.user.notifications.filter(id__in=ids)
        if action == 'mark_read':
            qs.update(is_read=True, read_at=timezone.now())
        elif action == 'delete':
            qs.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            unread_cnt = request.user.notifications.filter(is_read=False).count()
            total_cnt = request.user.notifications.count()
            return JsonResponse({'success': True, 'unread_count': unread_cnt, 'total_count': total_cnt})

        messages.success(request, f'Bulk action "{action}" completed successfully.')
    return redirect('notifications:list')


@login_required
def toggle_preference_api(request):
    if request.method == 'POST':
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        field = request.POST.get('field')
        value = request.POST.get('value')
        is_true = value in ['true', '1', True]

        allowed_fields = [
            'email_notifications', 'browser_notifications', 'task_updates',
            'project_updates', 'message_notifications', 'overtime_notifications',
            'system_notifications'
        ]
        if field in allowed_fields:
            setattr(pref, field, is_true)
            pref.save()
            return JsonResponse({'success': True, 'field': field, 'value': is_true})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def notification_preferences_view(request):
    pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        pref.email_notifications = 'email_notifications' in request.POST
        pref.browser_notifications = 'browser_notifications' in request.POST
        pref.task_updates = 'task_updates' in request.POST
        pref.project_updates = 'project_updates' in request.POST
        pref.message_notifications = 'message_notifications' in request.POST
        pref.overtime_notifications = 'overtime_notifications' in request.POST
        pref.system_notifications = 'system_notifications' in request.POST
        pref.save()
        messages.success(request, 'Notification preferences updated.')
        return redirect('notifications:preferences')

    return render(request, 'notifications/preferences.html', {'preferences': pref})
