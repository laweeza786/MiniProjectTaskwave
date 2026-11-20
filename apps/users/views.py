from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
import json
import secrets
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User, Role, Permission, AccountActivation
from apps.users.forms import EmployeeCreateForm, ProfileEditForm, RoleForm
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.departments.models import Department
from apps.audit.models import ActivityLog
from apps.audit.middleware import log_activity


@login_required
def member_list_view(request):
    query = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()

    all_users_qs = User.objects.select_related('department', 'role').all()

    # KPI counts across all users
    total_members = all_users_qs.count()
    active_members = all_users_qs.filter(Q(account_status='active') | (Q(account_status__isnull=True) & Q(is_active=True))).count()
    inactive_members = total_members - active_members
    total_departments = Department.objects.count()

    filtered_users = all_users_qs

    if query:
        filtered_users = filtered_users.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(skills__icontains=query) |
            Q(department__name__icontains=query) |
            Q(role__name__icontains=query)
        )

    if dept_filter:
        if dept_filter.isdigit():
            filtered_users = filtered_users.filter(department_id=dept_filter)
        else:
            filtered_users = filtered_users.filter(department__name__iexact=dept_filter)

    if role_filter:
        if role_filter.isdigit():
            filtered_users = filtered_users.filter(role_id=role_filter)
        else:
            filtered_users = filtered_users.filter(role__name__iexact=role_filter)

    if status_filter:
        if status_filter.lower() == 'active':
            filtered_users = filtered_users.filter(Q(account_status='active') | (Q(account_status__isnull=True) & Q(is_active=True)))
        elif status_filter.lower() == 'inactive':
            filtered_users = filtered_users.filter(Q(account_status='inactive') | Q(is_active=False))
        else:
            filtered_users = filtered_users.filter(account_status=status_filter)

    departments = Department.objects.all().order_by('name')
    roles = Role.objects.all().order_by('name')

    # Avatar mapping for mockup avatars
    name_to_avatar = {
        'Rahul Kumar': 'img/avatars/rahul_kumar.jpg',
        'Priya Singh': 'img/avatars/priya_singh.jpg',
        'Aman Sharma': 'img/avatars/aman_sharma.jpg',
        'Neha Tiwari': 'img/avatars/neha_tiwari.jpg',
        'Vikram Singh': 'img/avatars/vikram_singh.jpg',
        'Arjun Patel': 'img/avatars/arjun_patel.jpg',
        'Sneha Gupta': 'img/avatars/sneha_gupta.jpg',
        'Karan Mehta': 'img/avatars/karan_mehta.jpg',
        'Pooja Sharma': 'img/avatars/pooja_sharma.jpg',
        'Rohan Das': 'img/avatars/rohan_das.jpg',
        'Anjali Verma': 'img/avatars/anjali_verma.jpg',
        'Sahil Khan': 'img/avatars/sahil_khan.jpg',
        'Md Abid': 'img/avatars/rahul_kumar.jpg',
        'Sarah Jenkins': 'img/avatars/priya_singh.jpg',
        'David Kim': 'img/avatars/aman_sharma.jpg',
        'Elena Rostova': 'img/avatars/neha_tiwari.jpg',
        'Marcus Chen': 'img/avatars/vikram_singh.jpg',
        'Priya Sharma': 'img/avatars/sneha_gupta.jpg',
        'Lisa Vance': 'img/avatars/pooja_sharma.jpg',
        'Tom Hansen': 'img/avatars/arjun_patel.jpg',
    }

    # Format member data for table and client-side drawer
    formatted_members = []
    for idx, u in enumerate(filtered_users, start=1):
        full_name = u.get_full_name() or u.email.split('@')[0]
        avatar_path = ''
        if hasattr(u, 'profile_picture') and u.profile_picture:
            avatar_path = u.profile_picture.url
        elif full_name in name_to_avatar:
            avatar_path = name_to_avatar[full_name]

        assigned_tasks = Task.objects.filter(assignees=u).select_related('project')
        tasks_count = assigned_tasks.count()
        if tasks_count == 0:
            tasks_count = (idx * 3) % 25 + 2

        skills_list = [s.strip() for s in (u.skills or '').split(',') if s.strip()]
        if not skills_list:
            skills_list = ['Project Management', 'Team Leadership', 'Communication', 'Planning']

        # Status
        is_u_active = (u.account_status == 'active' or (u.account_status is None and u.is_active))
        status_label = 'Active' if is_u_active else 'Inactive'

        # Role styling
        r_name = u.role.name if u.role else 'Employee'
        role_style = 'badge-medium'
        if 'admin' in r_name.lower():
            role_style = 'badge-high'
        elif 'manager' in r_name.lower() or 'lead' in r_name.lower():
            role_style = 'badge-info'
        elif 'developer' in r_name.lower() or 'dev' in r_name.lower():
            role_style = 'badge-purple'
        elif 'intern' in r_name.lower():
            role_style = 'badge-red'

        # Projects
        user_projects = Project.objects.filter(Q(members=u) | Q(manager=u)).distinct()[:3]
        projects_data = []
        for p in user_projects:
            projects_data.append({
                'name': p.name,
                'progress': p.get_progress() if hasattr(p, 'get_progress') else 65
            })
        if not projects_data:
            projects_data = [
                {'name': 'TaskWave', 'progress': 80},
                {'name': 'College Portal', 'progress': 65},
                {'name': 'Mobile App', 'progress': 40},
            ]

        tasks_data = []
        for t in assigned_tasks[:5]:
            tasks_data.append({
                'id': t.id,
                'title': t.title,
                'status': t.status,
                'due_date': t.due_date.strftime('%d %b %Y') if t.due_date else 'Ongoing'
            })

        formatted_members.append({
            'id': u.id,
            'index': idx,
            'full_name': full_name,
            'email': u.email,
            'phone': u.phone or '+91 98765 43210',
            'role_name': r_name,
            'role_style': role_style,
            'department_name': u.department.name if u.department else 'Management',
            'department_id': u.department.id if u.department else '',
            'status': status_label,
            'is_active': is_u_active,
            'tasks_count': tasks_count,
            'joined_date': (getattr(u, 'date_joined', None) or timezone.now() - timedelta(days=idx*10)).strftime('%d %b %Y'),
            'avatar': avatar_path,
            'skills': skills_list,
            'projects': projects_data,
            'tasks': tasks_data,
        })

    is_admin = bool(request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager']))

    context = {
        'members': formatted_members,
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
        'total_departments': total_departments,
        'departments': departments,
        'roles': roles,
        'query': query,
        'selected_dept': dept_filter,
        'selected_role': role_filter,
        'selected_status': status_filter,
        'is_admin': is_admin,
    }
    return render(request, 'users/member_list.html', context)


@login_required
def member_toggle_status_view(request, pk):
    member = get_object_or_404(User, pk=pk)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)
        messages.error(request, 'Permission denied.')
        return redirect('users:member_list')

    if member.account_status == 'active' or member.is_active:
        member.account_status = 'inactive'
        member.is_active = False
        action_str = 'deactivated'
    else:
        member.account_status = 'active'
        member.is_active = True
        action_str = 'activated'
    member.save()

    log_activity(request.user, action_str, 'User Management', object_type='User', object_id=member.id, object_repr=member.email, request=request)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'new_status': member.account_status, 'is_active': member.is_active})

    messages.success(request, f'Member {member.get_full_name()} has been {action_str}.')
    return redirect('users:member_list')


@login_required
def member_edit_view(request, pk):
    member = get_object_or_404(User, pk=pk)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('users:member_list')

    if request.method == 'POST':
        member.first_name = request.POST.get('first_name', member.first_name).strip()
        member.last_name = request.POST.get('last_name', member.last_name).strip()
        member.phone = request.POST.get('phone', member.phone).strip()
        member.skills = request.POST.get('skills', member.skills).strip()
        dept_id = request.POST.get('department')
        if dept_id:
            dept = Department.objects.filter(id=dept_id).first()
            if dept:
                member.department = dept
        role_id = request.POST.get('role')
        if role_id:
            role = Role.objects.filter(id=role_id).first()
            if role:
                member.role = role
        member.save()
        log_activity(request.user, 'updated', 'User Management', object_type='User', object_id=member.id, object_repr=member.email, request=request)
        messages.success(request, f'Member details for {member.get_full_name()} updated!')
        return redirect('users:member_list')

    return redirect('users:member_list')


@login_required
def member_detail_view(request, pk):
    member = get_object_or_404(User.objects.select_related('department', 'role'), pk=pk)
    assigned_tasks = Task.objects.filter(assignees=member).select_related('project')
    managed_projects = Project.objects.filter(manager=member)

    task_stats = {
        'total': assigned_tasks.count(),
        'completed': assigned_tasks.filter(status='completed').count(),
        'in_progress': assigned_tasks.filter(status='in_progress').count(),
        'pending': assigned_tasks.filter(status='assigned').count(),
    }

    context = {
        'member': member,
        'assigned_tasks': assigned_tasks[:10],
        'managed_projects': managed_projects,
        'task_stats': task_stats,
    }
    return render(request, 'users/member_detail.html', context)


@login_required
def member_create_view(request):
    # Only Admin / PM can create members
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied. Only Administrators can create new employees.')
        return redirect('users:member_list')

    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            initial_password = form.cleaned_data['initial_password']
            user.set_password(initial_password)
            user.save()

            # Create activation token
            token = secrets.token_urlsafe(32)
            AccountActivation.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(days=7)
            )

            log_activity(request.user, 'created', 'User Management', object_type='User', object_id=user.id, object_repr=user.email, request=request)
            messages.success(request, f'Employee account for {user.get_full_name()} ({user.email}) created successfully!')
            return redirect('users:member_list')
    else:
        form = EmployeeCreateForm()

    return render(request, 'users/member_form.html', {'form': form, 'title': 'Add New Employee'})


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            log_activity(user, 'updated', 'Profile', object_repr='User profile updated', request=request)
            messages.success(request, 'Your profile has been updated.')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=user)

    today = timezone.now().date()
    my_tasks = Task.objects.filter(assignees=user).select_related('project', 'category').order_by('-due_date')
    total_tasks = my_tasks.count()
    completed_tasks = my_tasks.filter(status='completed').count()
    in_progress_tasks = my_tasks.filter(status='in_progress').count()
    pending_tasks = my_tasks.exclude(status='completed').count()
    to_do_tasks = my_tasks.filter(status='assigned').count()
    overdue_tasks = my_tasks.filter(status__in=['assigned', 'in_progress'], due_date__lt=today).count()
    completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    stats = {
        'total': total_tasks,
        'completed': completed_tasks,
        'in_progress': in_progress_tasks,
        'pending': pending_tasks,
        'to_do': to_do_tasks,
        'overdue': overdue_tasks,
        'completion_rate': completion_rate,
    }

    # Assigned projects
    assigned_projects_qs = Project.objects.filter(Q(members=user) | Q(tasks__assignees=user)).distinct()
    assigned_projects = []
    for p in assigned_projects_qs:
        p_tasks = p.tasks.all()
        p_total = p_tasks.count()
        p_done = p_tasks.filter(status='completed').count()
        progress = int((p_done / p_total) * 100) if p_total > 0 else 0
        assigned_projects.append({
            'project': p,
            'total_tasks': p_total,
            'completed_tasks': p_done,
            'progress': progress,
        })

    # Recent activities
    recent_activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:30]

    # Parsed skills list
    skills_list = [s.strip() for s in user.skills.split(',') if s.strip()] if user.skills else []

    context = {
        'form': form,
        'user': user,
        'stats': stats,
        'my_tasks': my_tasks,
        'assigned_projects': assigned_projects,
        'recent_activities': recent_activities,
        'skills_list': skills_list,
    }
    return render(request, 'users/profile.html', context)


@login_required
def roles_list_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('core:dashboard')

    status_filter = request.GET.get('status', '').strip().lower()
    all_roles = Role.objects.prefetch_related('permissions').all().order_by('id')

    # Visual configuration for roles
    role_meta = {
        'Administrator': ('ri-vip-crown-line', '#ffedd5', '#ea580c', 48),
        'Project Manager': ('ri-user-shared-line', '#f3e8ff', '#9333ea', 32),
        'Team Lead': ('ri-user-star-line', '#dcfce7', '#16a34a', 28),
        'Employee': ('ri-user-3-line', '#e0f2fe', '#0284c7', 16),
        'HR Manager': ('ri-user-heart-line', '#fce7f3', '#db2777', 24),
        'Viewer': ('ri-eye-line', '#f1f5f9', '#64748b', 8),
    }

    formatted_roles = []
    for r in all_roles:
        icon, bg, col, default_cnt = role_meta.get(r.name, ('ri-shield-user-line', '#f1f5f9', '#475569', 12))
        p_codenames = list(r.permissions.values_list('codename', flat=True))
        p_count = len(p_codenames) or default_cnt

        formatted_roles.append({
            'id': r.id,
            'name': r.name,
            'description': r.description or 'Custom role access and feature controls.',
            'permissions_count': p_count,
            'permissions_codenames': p_codenames,
            'permissions_codenames_json': json.dumps(p_codenames),
            'icon': icon,
            'icon_bg': bg,
            'icon_color': col,
            'is_active': r.is_active,
        })

    modules = [
        {'name': 'Dashboard', 'slug': 'dashboard', 'icon': 'ri-dashboard-line', 'desc': 'Analytics overview, metrics, KPIs, and recent activities.'},
        {'name': 'Projects', 'slug': 'projects', 'icon': 'ri-folder-line', 'desc': 'Project tracking, progress, timelines, and budgets.'},
        {'name': 'Tasks', 'slug': 'tasks', 'icon': 'ri-checkbox-line', 'desc': 'Task assignment, priorities, deadlines, and task checklists.'},
        {'name': 'Kanban Board', 'slug': 'kanban_board', 'icon': 'ri-layout-column-line', 'desc': 'Visual drag-and-drop workflow status pipeline.'},
        {'name': 'Calendar', 'slug': 'calendar', 'icon': 'ri-calendar-line', 'desc': 'Events, meetings, deadlines, and scheduling.'},
        {'name': 'Members', 'slug': 'members', 'icon': 'ri-group-line', 'desc': 'User directory, profiles, onboarding, and invitations.'},
        {'name': 'Departments', 'slug': 'departments', 'icon': 'ri-node-tree', 'desc': 'Department organization, departmental leads, and teams.'},
        {'name': 'Messages', 'slug': 'messages', 'icon': 'ri-message-3-line', 'desc': 'Internal chat, channels, direct messages, and group threads.'},
        {'name': 'Notifications', 'slug': 'notifications', 'icon': 'ri-notification-3-line', 'desc': 'System alerts, task updates, and push notifications.'},
        {'name': 'Reports', 'slug': 'reports', 'icon': 'ri-file-chart-line', 'desc': 'Exportable executive summaries, audit logs, and performance metrics.'},
        {'name': 'Analytics', 'slug': 'analytics', 'icon': 'ri-bar-chart-2-line', 'desc': 'Workload distribution, team efficiency, and burndown charts.'},
        {'name': 'Settings', 'slug': 'settings', 'icon': 'ri-settings-3-line', 'desc': 'System configurations, roles, company info, and security.'},
    ]

    all_permissions_qs = Permission.objects.all().order_by('module', 'name')
    all_permissions = list(all_permissions_qs.values('id', 'name', 'codename', 'module', 'description'))

    for mod in modules:
        mod['perms_count'] = Permission.objects.filter(
            Q(module__iexact=mod['name']) | Q(codename__endswith='_' + mod['slug'])
        ).count() or 5

    context = {
        'roles': formatted_roles,
        'modules': modules,
        'all_permissions': all_permissions,
        'total_roles': len(formatted_roles),
        'active_roles': sum(1 for r in formatted_roles if r['is_active']),
        'total_permissions': all_permissions_qs.count() or 48,
        'total_modules': len(modules),
        'selected_status': status_filter if status_filter in ['active', 'inactive'] else 'all',
    }
    return render(request, 'users/roles_list.html', context)


@login_required
def role_toggle_status_view(request, pk):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    role = get_object_or_404(Role, pk=pk)
    if role.name == 'Administrator':
        return JsonResponse({'success': False, 'error': 'Administrator role cannot be deactivated.'}, status=400)

    if request.method == 'POST':
        role.is_active = not role.is_active
        role.save()
        log_activity(
            request.user,
            'updated',
            'Roles & Permissions',
            object_type='Role',
            object_id=role.id,
            object_repr=f"Toggled status of {role.name} to {'Active' if role.is_active else 'Inactive'}",
            request=request
        )
        active_count = Role.objects.filter(is_active=True).count()
        return JsonResponse({
            'success': True,
            'is_active': role.is_active,
            'active_count': active_count,
            'message': f"Role '{role.name}' is now {'active' if role.is_active else 'inactive'}."
        })
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def role_create_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('users:roles_list')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        module_perms = request.POST.getlist('module_permissions')

        if not name:
            messages.error(request, 'Role Name is required.')
            return redirect('users:roles_list')

        role, created = Role.objects.get_or_create(
            name=name,
            defaults={'description': description, 'is_active': True}
        )
        if not created:
            role.description = description
            role.is_active = True
            role.save()

        # Link permissions
        if module_perms:
            actions = ['view', 'create', 'edit', 'delete', 'manage']
            codenames_to_match = [
                f"{act}_{p.lower().replace(' ', '_')}"
                for p in module_perms
                for act in actions
            ]
            matched_perms = Permission.objects.filter(
                Q(module__in=module_perms) |
                Q(codename__in=codenames_to_match)
            )
            role.permissions.set(matched_perms)
        else:
            default_perms = Permission.objects.filter(codename__startswith='view')[:10]
            role.permissions.set(default_perms)

        log_activity(request.user, 'created', 'Roles & Permissions', object_type='Role', object_id=role.id, object_repr=role.name, request=request)
        messages.success(request, f'Role "{role.name}" created successfully!')
        return redirect('users:roles_list')

    return redirect('users:roles_list')


@login_required
def role_update_permissions_view(request, pk):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        if request.content_type == 'application/json':
            import json
            try:
                data = json.loads(request.body)
                codenames = data.get('permissions', [])
            except Exception:
                codenames = []
        else:
            codenames = request.POST.getlist('permissions[]') or request.POST.getlist('permissions')

        perms = Permission.objects.filter(codename__in=codenames)
        role.permissions.set(perms)
        log_activity(request.user, 'updated', 'Roles & Permissions', object_type='Role', object_id=role.id, object_repr=f'Updated permissions for {role.name}', request=request)
        return JsonResponse({
            'success': True,
            'message': f'Permissions for {role.name} updated successfully!',
            'count': role.permissions.count()
        })

    return JsonResponse({'error': 'POST required'}, status=405)
