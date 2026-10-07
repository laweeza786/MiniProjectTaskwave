from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.notifications.models import Notification, NotificationPreference


@login_required
def notification_list_view(request):
    notifications = request.user.notifications.all()
    filter_type = request.GET.get('type')
    if filter_type:
        notifications = notifications.filter(notification_type=filter_type)

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count(),
    })


@login_required
def mark_all_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:list')


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
        pref.save()
        messages.success(request, 'Notification preferences updated.')
        return redirect('notifications:preferences')

    return render(request, 'notifications/preferences.html', {'preferences': pref})
