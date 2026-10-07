"""
TaskWave - Global Context Processors
Provides user data, notification count, unread message count, and system settings to all templates.
"""
from apps.audit.models import SystemSettings
from apps.notifications.models import Notification
from apps.messaging.models import Conversation


def global_context(request):
    context = {
        'system_settings': SystemSettings.get_settings() if hasattr(SystemSettings, 'get_settings') else None,
        'unread_notifications_count': 0,
        'unread_messages_count': 0,
    }
    
    if request.user.is_authenticated:
        try:
            context['unread_notifications_count'] = Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count()
        except Exception:
            context['unread_notifications_count'] = 0

        try:
            context['unread_messages_count'] = Conversation.objects.filter(
                members=request.user
            ).filter(
                messages__messagestatus__user=request.user,
                messages__messagestatus__is_read=False
            ).distinct().count()
        except Exception:
            context['unread_messages_count'] = 0

    return context
