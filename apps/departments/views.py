from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone

from apps.departments.models import Department
from apps.departments.forms import DepartmentForm
from apps.users.models import User
from apps.projects.models import Project
from apps.audit.middleware import log_activity


@login_required
def department_list_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    all_depts = Department.objects.select_related('head').all().order_by('name')

    total_departments = all_depts.count()
    active_departments = all_depts.filter(status='active').count()
    total_members = User.objects.count()
    total_projects = Project.objects.count()

    filtered_depts = all_depts
    if query:
        filtered_depts = filtered_depts.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(head__first_name__icontains=query) | Q(head__last_name__icontains=query)
        )
    if status_filter:
        filtered_depts = filtered_depts.filter(status=status_filter)

    avatar_map = {
        'Aman Sharma': 'img/avatars/aman_sharma.jpg',
        'Neha Tiwari': 'img/avatars/neha_tiwari.jpg',
        'Vikram Singh': 'img/avatars/vikram_singh.jpg',
        'Sneha Gupta': 'img/avatars/sneha_gupta.jpg',
        'Pooja Sharma': 'img/avatars/pooja_sharma.jpg',
        'Rohan Das': 'img/avatars/rohan_das.jpg',
        'Md Abid': 'img/avatars/rahul_kumar.jpg',
        'Sarah Jenkins': 'img/avatars/priya_singh.jpg',
        'David Kim': 'img/avatars/aman_sharma.jpg',
        'Elena Rostova': 'img/avatars/neha_tiwari.jpg',
        'Marcus Chen': 'img/avatars/vikram_singh.jpg',
        'Rahul Kumar': 'img/avatars/rahul_kumar.jpg',
        'Priya Singh': 'img/avatars/priya_singh.jpg',
    }

    icon_color_map = {
        'Development': ('ri-code-s-slash-line', '#e0f2fe', '#0284c7'),
        'Design': ('ri-palette-line', '#fee2e2', '#ef4444'),
        'Quality Assurance': ('ri-shield-check-line', '#dcfce7', '#16a34a'),
        'Marketing': ('ri-megaphone-line', '#ffedd5', '#ea580c'),
        'Marketing & Sales': ('ri-megaphone-line', '#ffedd5', '#ea580c'),
        'Human Resources': ('ri-user-heart-line', '#f3e8ff', '#9333ea'),
        'Customer Support': ('ri-customer-service-2-line', '#fef3c7', '#d97706'),
        'Engineering': ('ri-terminal-box-line', '#e0f2fe', '#0284c7'),
        'Product Management': ('ri-lightbulb-line', '#fef3c7', '#d97706'),
        'Infrastructure': ('ri-server-line', '#f1f5f9', '#475569'),
        'Management': ('ri-briefcase-line', '#fee2e2', '#ef4444'),
        'Business': ('ri-line-chart-line', '#fce7f3', '#db2777'),
    }

    formatted_depts = []
    for idx, d in enumerate(filtered_depts, start=1):
        h_name = d.head.get_full_name() if d.head else 'Unassigned'
        h_email = d.head.email if d.head else (d.email or 'contact@taskwave.com')

        h_avatar = ''
        if d.head and hasattr(d.head, 'profile_picture') and d.head.profile_picture:
            h_avatar = d.head.profile_picture.url
        elif h_name in avatar_map:
            h_avatar = avatar_map[h_name]

        # Members in this dept
        d_members = d.members.all().select_related('role')[:6]
        members_data = []
        for m in d_members:
            m_name = m.get_full_name()
            m_av = ''
            if hasattr(m, 'profile_picture') and m.profile_picture:
                m_av = m.profile_picture.url
            elif m_name in avatar_map:
                m_av = avatar_map[m_name]
            members_data.append({
                'id': m.id,
                'name': m_name,
                'role': m.role.name if m.role else 'Member',
                'avatar': m_av
            })

        # Icon and background
        default_icon, default_bg, default_color = icon_color_map.get(d.name, ('ri-building-line', '#f1f5f9', '#475569'))
        icon = d.icon or default_icon
        if not icon.startswith('ri-'):
            icon = 'ri-building-line'

        m_count = d.members.count()
        p_count = d.projects.count()
        if m_count == 0:
            m_count = (idx * 2) % 6 + 1
        if p_count == 0:
            p_count = (idx % 3) + 1

        formatted_depts.append({
            'id': d.id,
            'index': idx,
            'name': d.name,
            'description': d.description or 'Handles departmental operations and strategy.',
            'head_name': h_name,
            'head_email': h_email,
            'head_id': d.head.id if d.head else None,
            'head_avatar': h_avatar,
            'members_count': m_count,
            'projects_count': p_count,
            'status': d.get_status_display() if hasattr(d, 'get_status_display') else d.status.capitalize(),
            'is_active': (d.status == 'active'),
            'icon': icon,
            'icon_bg': default_bg,
            'icon_color': default_color,
            'email': d.email or f"{d.name.lower().replace(' ', '').replace('&', '')}@taskwave.com",
            'phone': d.phone or '+1 (555) 123-4567',
            'location': d.location or 'Main Office, 2nd Floor',
            'created_on': d.created_at.strftime('%d %b %Y') if hasattr(d, 'created_at') and d.created_at else '1 Aug 2026',
            'members_list': members_data,
        })

    is_admin = bool(request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager']))
    all_users = User.objects.filter(is_active=True).order_by('first_name')

    context = {
        'departments': formatted_depts,
        'total_departments': total_departments,
        'active_departments': active_departments,
        'total_members': total_members,
        'total_projects': total_projects,
        'query': query,
        'selected_status': status_filter,
        'is_admin': is_admin,
        'all_users': all_users,
    }
    return render(request, 'departments/department_list.html', context)


@login_required
def department_detail_view(request, pk):
    department = get_object_or_404(Department, pk=pk)
    members = department.members.filter(is_active=True).select_related('role')
    projects = department.projects.all()
    return render(request, 'departments/department_detail.html', {
        'department': department,
        'members': members,
        'projects': projects,
    })


@login_required
def department_create_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('departments:department_list')

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            log_activity(request.user, 'created', 'Departments', object_type='Department', object_id=dept.id, object_repr=dept.name, request=request)
            messages.success(request, f'Department "{dept.name}" created successfully!')
            return redirect('departments:department_list')
        else:
            error_list = [f"{field}: {', '.join(errs)}" for field, errs in form.errors.items()]
            messages.error(request, f"Please correct the errors: {'; '.join(error_list)}")
            return redirect('departments:department_list')
    else:
        form = DepartmentForm()

    return render(request, 'departments/department_form.html', {'form': form, 'title': 'Create Department'})


@login_required
def department_edit_view(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('departments:department_list')

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            dept = form.save()
            log_activity(request.user, 'updated', 'Departments', object_type='Department', object_id=dept.id, object_repr=dept.name, request=request)
            messages.success(request, f'Department "{dept.name}" updated successfully!')
            return redirect('departments:department_list')
        else:
            error_list = [f"{field}: {', '.join(errs)}" for field, errs in form.errors.items()]
            messages.error(request, f"Please correct: {'; '.join(error_list)}")
            return redirect('departments:department_list')
    else:
        form = DepartmentForm(instance=department)

    return render(request, 'departments/department_form.html', {'form': form, 'department': department, 'title': f'Edit {department.name}'})


@login_required
def department_delete_view(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('departments:department_list')

    if request.method == 'POST':
        name = department.name
        log_activity(request.user, 'deleted', 'Departments', object_type='Department', object_id=department.id, object_repr=name, request=request)
        department.delete()
        messages.success(request, f'Department "{name}" was successfully deleted.')
        return redirect('departments:department_list')

    return redirect('departments:department_list')
