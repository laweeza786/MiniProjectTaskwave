from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
import secrets
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User, Role, Permission, AccountActivation
from apps.users.forms import EmployeeCreateForm, ProfileEditForm, RoleForm
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.departments.models import Department
from apps.audit.middleware import log_activity


@login_required
def member_list_view(request):
    query = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('department', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    users = User.objects.select_related('department', 'role').all()

    if query:
        users = users.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query) | Q(skills__icontains=query))
    if dept_filter:
        users = users.filter(department_id=dept_filter)
    if role_filter:
        users = users.filter(role_id=role_filter)
    if status_filter:
        users = users.filter(account_status=status_filter)

    departments = Department.objects.all()
    roles = Role.objects.all()

    context = {
        'members': users,
        'total_members': users.count(),
        'departments': departments,
        'roles': roles,
        'query': query,
        'selected_dept': dept_filter,
        'selected_role': role_filter,
    }
    return render(request, 'users/member_list.html', context)


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

    my_tasks = Task.objects.filter(assignees=user)
    stats = {
        'total': my_tasks.count(),
        'completed': my_tasks.filter(status='completed').count(),
        'in_progress': my_tasks.filter(status='in_progress').count(),
    }

    return render(request, 'users/profile.html', {'form': form, 'stats': stats, 'user': user})


@login_required
def roles_list_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied.')
        return redirect('core:dashboard')

    roles = Role.objects.prefetch_related('permissions').all()
    permissions = Permission.objects.all().order_by('module')

    return render(request, 'users/roles_list.html', {'roles': roles, 'permissions': permissions})


@login_required
def role_create_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied.')
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            log_activity(request.user, 'created', 'Roles & Permissions', object_type='Role', object_id=role.id, object_repr=role.name, request=request)
            messages.success(request, f'Role "{role.name}" created!')
            return redirect('users:roles_list')
    else:
        form = RoleForm()

    return render(request, 'users/role_form.html', {'form': form, 'title': 'Create Role'})
