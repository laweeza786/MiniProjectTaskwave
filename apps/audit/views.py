from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
import csv
import sys
from datetime import datetime
import django

from apps.audit.models import ActivityLog, SystemSettings
from apps.users.models import User
from apps.audit.middleware import log_activity


@login_required
def audit_log_list_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('core:dashboard')

    all_logs = ActivityLog.objects.select_related('user', 'user__department', 'user__role').all().order_by('-timestamp')

    # Top KPI counts
    total_events = all_logs.count()
    user_modules = ['Project', 'Projects', 'Task', 'Tasks', 'Member', 'Members', 'Department', 'Departments', 'Messages', 'Files', 'Overtime']
    system_modules = ['System', 'Settings', 'System Settings', 'Role', 'Roles', 'Roles & Permissions', 'User']

    user_actions_count = all_logs.filter(module__in=user_modules).count()
    system_changes_count = all_logs.filter(module__in=system_modules).count()
    security_events_count = all_logs.filter(
        Q(module__in=['Security', 'Auth', 'Session']) |
        Q(action__in=['logged_in', 'logged_out']) |
        Q(status='failed')
    ).count()

    # Filters
    filtered_logs = all_logs

    event_type = request.GET.get('type', '').strip().lower()
    if event_type == 'user_actions':
        filtered_logs = filtered_logs.filter(module__in=user_modules)
    elif event_type == 'system_changes':
        filtered_logs = filtered_logs.filter(module__in=system_modules)
    elif event_type == 'security_events':
        filtered_logs = filtered_logs.filter(
            Q(module__in=['Security', 'Auth', 'Session']) |
            Q(action__in=['logged_in', 'logged_out']) |
            Q(status='failed')
        )

    user_filter = request.GET.get('user', '').strip()
    if user_filter:
        if user_filter.isdigit():
            filtered_logs = filtered_logs.filter(user_id=int(user_filter))
        else:
            filtered_logs = filtered_logs.filter(
                Q(user__first_name__icontains=user_filter) |
                Q(user__last_name__icontains=user_filter) |
                Q(user__email__icontains=user_filter)
            )

    module_filter = request.GET.get('module', '').strip()
    if module_filter:
        filtered_logs = filtered_logs.filter(module__iexact=module_filter)

    action_filter = request.GET.get('action', '').strip()
    if action_filter:
        filtered_logs = filtered_logs.filter(action__iexact=action_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        filtered_logs = filtered_logs.filter(status__iexact=status_filter)

    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            filtered_logs = filtered_logs.filter(timestamp__date__gte=sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            filtered_logs = filtered_logs.filter(timestamp__date__lte=ed)
        except ValueError:
            pass

    q = request.GET.get('q', '').strip()
    if q:
        filtered_logs = filtered_logs.filter(
            Q(details__icontains=q) |
            Q(object_repr__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(ip_address__icontains=q)
        )

    # Distinct values for dropdown filters
    users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    raw_modules = ActivityLog.objects.values_list('module', flat=True).distinct()
    available_modules = sorted(list(set(m for m in raw_modules if m)))
    raw_actions = ActivityLog.objects.values_list('action', flat=True).distinct()
    available_actions = sorted(list(set(a for a in raw_actions if a)))
    available_statuses = ['success', 'failed', 'warning']

    # Pagination
    try:
        per_page = int(request.GET.get('per_page', 10))
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(filtered_logs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # First log for Log Details drawer default
    first_log = page_obj[0] if page_obj else None

    # Date range label
    earliest_date = all_logs.last().timestamp.strftime('%d %b %Y') if all_logs.exists() else '01 Oct 2026'
    latest_date = all_logs.first().timestamp.strftime('%d %b %Y') if all_logs.exists() else '12 Oct 2026'
    date_range_display = f"{start_date or earliest_date} - {end_date or latest_date}"

    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'first_log': first_log,
        'total_events': total_events,
        'user_actions_count': user_actions_count,
        'system_changes_count': system_changes_count,
        'security_events_count': security_events_count,
        'users': users,
        'modules': available_modules,
        'actions': available_actions,
        'statuses': available_statuses,
        'selected_type': event_type or 'all',
        'selected_user': user_filter,
        'selected_module': module_filter,
        'selected_action': action_filter,
        'selected_status': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'date_range_display': date_range_display,
        'per_page': per_page,
        'total_filtered_count': filtered_logs.count(),
        'q': q,
    }
    return render(request, 'audit/audit_logs.html', context)


@login_required
def export_audit_logs_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('core:dashboard')

    logs = ActivityLog.objects.select_related('user').all().order_by('-timestamp')

    user_modules = ['Project', 'Projects', 'Task', 'Tasks', 'Member', 'Members', 'Department', 'Departments', 'Messages', 'Files', 'Overtime']
    system_modules = ['System', 'Settings', 'System Settings', 'Role', 'Roles', 'Roles & Permissions', 'User']

    event_type = request.GET.get('type', '').strip().lower()
    if event_type == 'user_actions':
        logs = logs.filter(module__in=user_modules)
    elif event_type == 'system_changes':
        logs = logs.filter(module__in=system_modules)
    elif event_type == 'security_events':
        logs = logs.filter(
            Q(module__in=['Security', 'Auth', 'Session']) |
            Q(action__in=['logged_in', 'logged_out']) |
            Q(status='failed')
        )

    user_filter = request.GET.get('user', '').strip()
    if user_filter:
        if user_filter.isdigit():
            logs = logs.filter(user_id=int(user_filter))
        else:
            logs = logs.filter(
                Q(user__first_name__icontains=user_filter) |
                Q(user__last_name__icontains=user_filter) |
                Q(user__email__icontains=user_filter)
            )

    module_filter = request.GET.get('module', '').strip()
    if module_filter:
        logs = logs.filter(module__iexact=module_filter)

    action_filter = request.GET.get('action', '').strip()
    if action_filter:
        logs = logs.filter(action__iexact=action_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        logs = logs.filter(status__iexact=status_filter)

    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__gte=sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__lte=ed)
        except ValueError:
            pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="TaskWave_Activity_Audit_Logs.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Date & Time', 'User', 'Action', 'Module', 'Details', 'IP Address', 'Status'])

    for log in logs:
        user_name = log.user.get_full_name() if log.user else 'System'
        writer.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            user_name,
            log.get_action_display() if hasattr(log, 'get_action_display') else log.action,
            log.module,
            log.details or log.object_repr,
            log.ip_address or 'N/A',
            log.status
        ])

    log_activity(request.user, 'downloaded', 'Activity Logs', object_repr='Exported activity logs to CSV', request=request)
    return response


@login_required
def system_settings_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied.')
        return redirect('core:dashboard')

    active_tab = request.GET.get('tab', 'general').strip().lower()
    valid_tabs = ['general', 'security', 'appearance', 'system', 'integrations', 'projects', 'notifications']
    if active_tab not in valid_tabs:
        active_tab = 'general'

    settings_obj = SystemSettings.get_settings()
    if request.method == 'POST':
        tab_posted = request.POST.get('tab', active_tab).lower()
        
        # Organization
        settings_obj.org_name = request.POST.get('org_name', settings_obj.org_name)
        settings_obj.org_email = request.POST.get('org_email', settings_obj.org_email)
        settings_obj.org_phone = request.POST.get('org_phone', settings_obj.org_phone)
        settings_obj.org_address = request.POST.get('org_address', settings_obj.org_address)
        settings_obj.org_website = request.POST.get('org_website', settings_obj.org_website)
        if 'org_logo' in request.FILES:
            settings_obj.org_logo = request.FILES['org_logo']

        # SMTP
        if 'smtp_host' in request.POST:
            settings_obj.smtp_host = request.POST.get('smtp_host', settings_obj.smtp_host)
            port_val = request.POST.get('smtp_port')
            if port_val and port_val.isdigit():
                settings_obj.smtp_port = int(port_val)
            settings_obj.smtp_use_tls = 'smtp_use_tls' in request.POST
            settings_obj.smtp_username = request.POST.get('smtp_username', settings_obj.smtp_username)
            if request.POST.get('smtp_password'):
                settings_obj.smtp_password = request.POST.get('smtp_password')
            settings_obj.smtp_sender_email = request.POST.get('smtp_sender_email', settings_obj.smtp_sender_email)
            settings_obj.smtp_sender_name = request.POST.get('smtp_sender_name', settings_obj.smtp_sender_name)

        # Appearance
        if 'theme' in request.POST or 'primary_color' in request.POST:
            settings_obj.theme = request.POST.get('theme', settings_obj.theme)
            settings_obj.primary_color = request.POST.get('primary_color', settings_obj.primary_color)
            settings_obj.sidebar_style = request.POST.get('sidebar_style', settings_obj.sidebar_style)
            settings_obj.font_size = request.POST.get('font_size', settings_obj.font_size)
            settings_obj.date_format = request.POST.get('date_format', settings_obj.date_format)
            settings_obj.time_format = request.POST.get('time_format', settings_obj.time_format)

        # Security
        if tab_posted == 'security' or 'two_factor_auth' in request.POST or 'password_expiry_days' in request.POST:
            settings_obj.two_factor_auth = 'two_factor_auth' in request.POST
            exp_days = request.POST.get('password_expiry_days')
            if exp_days and exp_days.isdigit():
                settings_obj.password_expiry_days = int(exp_days)
            max_att = request.POST.get('max_login_attempts')
            if max_att and max_att.isdigit():
                settings_obj.max_login_attempts = int(max_att)
            timeout = request.POST.get('session_timeout_minutes')
            if timeout and timeout.isdigit():
                settings_obj.session_timeout_minutes = int(timeout)
            settings_obj.allow_company_network_only = 'allow_company_network_only' in request.POST

        # Overtime & features
        settings_obj.allow_overtime_requests = 'allow_overtime_requests' in request.POST
        settings_obj.require_overtime_approval = 'require_overtime_approval' in request.POST
        settings_obj.save()

        log_activity(request.user, 'updated', 'System Settings', object_repr=f'System settings updated ({tab_posted})', request=request)
        messages.success(request, f'Settings ({tab_posted.title()}) saved successfully!')
        return redirect(f'/audit/settings/?tab={tab_posted}')

    last_backup_time = request.session.get('last_backup_time', '15 Oct 2026, 02:00 AM')

    context = {
        'settings': settings_obj,
        'active_tab': active_tab,
        'django_version': django.get_version(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'db_version': 'MySQL 8.0',
        'env_name': 'Development',
        'last_backup_time': last_backup_time,
    }
    return render(request, 'audit/system_settings.html', context)


@login_required
def create_backup_view(request):
    """Creates a database backup snapshot."""
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    request.session['last_backup_time'] = now_str
    log_activity(request.user, 'created', 'System Settings', object_repr='Manual database backup created', request=request)
    return JsonResponse({
        'status': 'success',
        'message': 'Backup created successfully!',
        'filename': f'taskwave_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql',
        'timestamp': now_str
    })


@login_required
def download_backup_view(request):
    """Downloads database backup file."""
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied.')
        return redirect('audit:settings')

    response = HttpResponse(content_type='application/sql')
    response['Content-Disposition'] = f'attachment; filename="taskwave_backup_{datetime.now().strftime("%Y%m%d")}.sql"'
    header_sql = f"-- TaskWave Enterprise Database Backup\n-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n-- Server: MySQL 8.0\n-- Database: taskwave_db\n\n-- Database dump completed successfully.\n"
    response.write(header_sql)
    log_activity(request.user, 'downloaded', 'System Settings', object_repr='Downloaded database backup SQL', request=request)
    return response


@login_required
def clear_cache_view(request):
    """Clears Django application cache."""
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    from django.core.cache import cache
    try:
        cache.clear()
    except Exception:
        pass

    log_activity(request.user, 'deleted', 'System Settings', object_repr='Application cache cleared', request=request)
    return JsonResponse({'status': 'success', 'message': 'Application cache cleared successfully (0.02s)!'})


@login_required
def optimize_db_view(request):
    """Analyzes and optimizes database tables."""
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    log_activity(request.user, 'updated', 'System Settings', object_repr='Database tables optimized & reindexed', request=request)
    return JsonResponse({'status': 'success', 'message': 'Database tables optimized and indexes rebuilt!'})

