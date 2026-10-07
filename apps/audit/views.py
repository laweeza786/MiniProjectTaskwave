from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.audit.models import ActivityLog, SystemSettings
from apps.users.models import User
from apps.audit.middleware import log_activity


@login_required
def audit_log_list_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied.')
        return redirect('core:dashboard')

    logs = ActivityLog.objects.select_related('user').all()

    action_filter = request.GET.get('action')
    module_filter = request.GET.get('module')
    user_filter = request.GET.get('user')
    status_filter = request.GET.get('status')

    if action_filter:
        logs = logs.filter(action=action_filter)
    if module_filter:
        logs = logs.filter(module=module_filter)
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    if status_filter:
        logs = logs.filter(status=status_filter)

    users = User.objects.filter(is_active=True)
    modules = ActivityLog.objects.values_list('module', flat=True).distinct()

    return render(request, 'audit/audit_logs.html', {
        'logs': logs[:100],
        'users': users,
        'modules': modules,
        'total_logs': logs.count(),
    })


@login_required
def system_settings_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied.')
        return redirect('core:dashboard')

    settings_obj = SystemSettings.get_settings()
    if request.method == 'POST':
        settings_obj.org_name = request.POST.get('org_name', settings_obj.org_name)
        settings_obj.org_email = request.POST.get('org_email', settings_obj.org_email)
        settings_obj.org_phone = request.POST.get('org_phone', settings_obj.org_phone)
        settings_obj.org_address = request.POST.get('org_address', settings_obj.org_address)
        settings_obj.primary_color = request.POST.get('primary_color', settings_obj.primary_color)
        settings_obj.theme = request.POST.get('theme', settings_obj.theme)
        settings_obj.two_factor_auth = 'two_factor_auth' in request.POST
        settings_obj.allow_overtime_requests = 'allow_overtime_requests' in request.POST
        settings_obj.require_overtime_approval = 'require_overtime_approval' in request.POST
        settings_obj.save()

        log_activity(request.user, 'updated', 'System Settings', object_repr='System settings updated', request=request)
        messages.success(request, 'System settings saved successfully!')
        return redirect('audit:settings')

    return render(request, 'audit/system_settings.html', {'settings': settings_obj})
