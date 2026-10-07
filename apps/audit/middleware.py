"""
TaskWave - Audit Log Middleware
Logs user actions and provides helper utilities for request-scoped auditing.
"""
from apps.audit.models import ActivityLog


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            request.client_ip = x_forwarded_for.split(',')[0].strip()
        else:
            request.client_ip = request.META.get('REMOTE_ADDR')

        request.user_agent_str = request.META.get('HTTP_USER_AGENT', '')[:500]

        response = self.get_response(request)
        return response


def log_activity(user, action, module, object_type='', object_id=None, object_repr='', details='', request=None, status='success'):
    """
    Utility function to log an activity in the database.
    """
    ip_address = None
    user_agent = ''
    if request:
        ip_address = getattr(request, 'client_ip', None) or request.META.get('REMOTE_ADDR')
        user_agent = getattr(request, 'user_agent_str', '') or request.META.get('HTTP_USER_AGENT', '')[:500]

    try:
        return ActivityLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            module=module,
            object_type=object_type,
            object_id=object_id,
            object_repr=str(object_repr)[:500],
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
    except Exception as e:
        # Don't let audit log failure break the request
        return None
