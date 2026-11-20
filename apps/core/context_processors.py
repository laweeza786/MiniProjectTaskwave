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
        user = request.user
        context['is_admin'] = user.is_admin_user
        context['is_pm'] = user.is_project_manager
        context['is_team_lead'] = user.is_team_lead
        context['is_employee'] = user.is_employee
        context['is_manager_or_above'] = user.is_manager_or_above
        context['is_lead_or_above'] = user.is_lead_or_above

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
    else:
        context['is_admin'] = False
        context['is_pm'] = False
        context['is_team_lead'] = False
        context['is_employee'] = False
        context['is_manager_or_above'] = False
        context['is_lead_or_above'] = False

    return context

