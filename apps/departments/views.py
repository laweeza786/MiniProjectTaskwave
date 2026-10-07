from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from apps.departments.models import Department
from apps.departments.forms import DepartmentForm
from apps.audit.middleware import log_activity


@login_required
def department_list_view(request):
    departments = Department.objects.annotate(
        members_count=Count('members', filter=Q(members__is_active=True)),
        projects_count=Count('projects')
    ).all()
    return render(request, 'departments/department_list.html', {'departments': departments})


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
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied.')
        return redirect('departments:department_list')

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            log_activity(request.user, 'created', 'Departments', object_type='Department', object_id=dept.id, object_repr=dept.name, request=request)
            messages.success(request, f'Department "{dept.name}" created!')
            return redirect('departments:department_list')
    else:
        form = DepartmentForm()

    return render(request, 'departments/department_form.html', {'form': form, 'title': 'Create Department'})


@login_required
def department_edit_view(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator')):
        messages.error(request, 'Permission denied.')
        return redirect('departments:department_list')

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            dept = form.save()
            log_activity(request.user, 'updated', 'Departments', object_type='Department', object_id=dept.id, object_repr=dept.name, request=request)
            messages.success(request, f'Department "{dept.name}" updated!')
            return redirect('departments:department_list')
    else:
        form = DepartmentForm(instance=department)

    return render(request, 'departments/department_form.html', {'form': form, 'department': department, 'title': f'Edit {department.name}'})
