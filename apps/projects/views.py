from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse

from apps.projects.models import Project, ProjectMember, ProjectMilestone
from apps.projects.forms import ProjectForm, ProjectMilestoneForm
from apps.tasks.models import Task
from apps.files.models import ProjectFile
from apps.users.models import User
from apps.audit.middleware import log_activity


@login_required
def project_list_view(request):
    user = request.user
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    department_filter = request.GET.get('department', '')

    projects = Project.objects.all()

    # Filter by user if not admin
    if not (user.is_superuser or (user.role and user.role.name in ['Administrator', 'Project Manager'])):
        projects = projects.filter(Q(members=user) | Q(manager=user) | Q(visibility='organization')).distinct()

    if query:
        projects = projects.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(project_key__icontains=query))
    if status_filter:
        projects = projects.filter(status=status_filter)
    if priority_filter:
        projects = projects.filter(priority=priority_filter)
    if department_filter:
        projects = projects.filter(department_id=department_filter)

    total_projects = 12
    active_count = 8
    completed_count = 3
    on_hold_count = 1

    sample_projects = [
        {
            'id': 1,
            'name': 'TaskWave',
            'is_starred': True,
            'subtitle': 'Main Task Management System',
            'icon': 'ri-macbook-line',
            'icon_bg': '#e0f2fe',
            'icon_color': '#0284c7',
            'progress': 80,
            'bar_color': '#22c55e',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'department': 'Development',
            'start_date': '1 Aug 2026',
            'end_date': '30 Nov 2026',
            'date_range': '1 Aug 2026 - 30 Nov 2026',
            'avatars': ['img/avatars/rahul_kumar.jpg', 'img/avatars/priya_singh.jpg', 'img/avatars/aman_sharma.jpg'],
            'extra_count': 5
        },
        {
            'id': 2,
            'name': 'College Portal',
            'is_starred': False,
            'subtitle': 'Academic Management System',
            'icon': 'ri-bank-line',
            'icon_bg': '#f1f5f9',
            'icon_color': '#475569',
            'progress': 65,
            'bar_color': '#f59e0b',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'department': 'Academic',
            'start_date': '15 Jul 2026',
            'end_date': '15 Oct 2026',
            'date_range': '15 Jul 2026 - 15 Oct 2026',
            'avatars': ['img/avatars/neha_tiwari.jpg', 'img/avatars/vikram_singh.jpg', 'img/avatars/sahil_khan.jpg'],
            'extra_count': 3
        },
        {
            'id': 3,
            'name': 'Mobile App',
            'is_starred': False,
            'subtitle': 'Android Application',
            'icon': 'ri-smartphone-line',
            'icon_bg': '#fee2e2',
            'icon_color': '#ef4444',
            'progress': 40,
            'bar_color': '#ea580c',
            'status': 'On Hold',
            'status_class': 'badge-on-hold',
            'department': 'Development',
            'start_date': '1 Sep 2026',
            'end_date': '31 Dec 2026',
            'date_range': '1 Sep 2026 - 31 Dec 2026',
            'avatars': ['img/avatars/priya_singh.jpg', 'img/avatars/rahul_kumar.jpg'],
            'extra_count': 2
        },
        {
            'id': 4,
            'name': 'Website Redesign',
            'is_starred': False,
            'subtitle': 'Marketing Website',
            'icon': 'ri-global-line',
            'icon_bg': '#dbeafe',
            'icon_color': '#2563eb',
            'progress': 100,
            'bar_color': '#22c55e',
            'status': 'Completed',
            'status_class': 'badge-completed',
            'department': 'Marketing',
            'start_date': '1 Jun 2026',
            'end_date': '31 Aug 2026',
            'date_range': '1 Jun 2026 - 31 Aug 2026',
            'avatars': ['img/avatars/aman_sharma.jpg', 'img/avatars/neha_tiwari.jpg', 'img/avatars/vikram_singh.jpg'],
            'extra_count': 4
        },
        {
            'id': 5,
            'name': 'Database Optimization',
            'is_starred': False,
            'subtitle': 'System Performance',
            'icon': 'ri-database-2-line',
            'icon_bg': '#ffedd5',
            'icon_color': '#ea580c',
            'progress': 30,
            'bar_color': '#ef4444',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'department': 'IT',
            'start_date': '1 Oct 2026',
            'end_date': '31 Dec 2026',
            'date_range': '1 Oct 2026 - 31 Dec 2026',
            'avatars': ['img/avatars/rahul_kumar.jpg', 'img/avatars/aman_sharma.jpg'],
            'extra_count': 2
        },
        {
            'id': 6,
            'name': 'API Integration',
            'is_starred': False,
            'subtitle': 'Third Party Integrations',
            'icon': 'ri-shield-check-line',
            'icon_bg': '#fef2f2',
            'icon_color': '#dc2626',
            'progress': 50,
            'bar_color': '#f59e0b',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'department': 'Development',
            'start_date': '15 Aug 2026',
            'end_date': '30 Nov 2026',
            'date_range': '15 Aug 2026 - 30 Nov 2026',
            'avatars': ['img/avatars/priya_singh.jpg', 'img/avatars/sahil_khan.jpg', 'img/avatars/neha_tiwari.jpg'],
            'extra_count': 3
        },
        {
            'id': 7,
            'name': 'Documentation',
            'is_starred': False,
            'subtitle': 'Project Documentation',
            'icon': 'ri-file-text-line',
            'icon_bg': '#dcfce7',
            'icon_color': '#16a34a',
            'progress': 90,
            'bar_color': '#22c55e',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'department': 'Documentation',
            'start_date': '1 Aug 2026',
            'end_date': '31 Oct 2026',
            'date_range': '1 Aug 2026 - 31 Oct 2026',
            'avatars': ['img/avatars/vikram_singh.jpg', 'img/avatars/rahul_kumar.jpg'],
            'extra_count': 1
        },
        {
            'id': 8,
            'name': 'Internal Tools',
            'is_starred': False,
            'subtitle': 'Company Internal Tools',
            'icon': 'ri-tools-line',
            'icon_bg': '#f1f5f9',
            'icon_color': '#475569',
            'progress': 20,
            'bar_color': '#ef4444',
            'status': 'Planning',
            'status_class': 'badge-planning',
            'department': 'Infrastructure',
            'start_date': '1 Nov 2026',
            'end_date': '31 Jan 2027',
            'date_range': '1 Nov 2026 - 31 Jan 2027',
            'avatars': ['img/avatars/arjun_patel.jpg', 'img/avatars/pooja_sharma.jpg'],
            'extra_count': 2
        }
    ]

    context = {
        'projects': projects,
        'sample_projects': sample_projects,
        'total_projects': total_projects,
        'active_count': active_count,
        'completed_count': completed_count,
        'on_hold_count': on_hold_count,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'query': query,
    }
    return render(request, 'projects/project_list.html', context)


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    tasks = project.tasks.all().order_by('-created_at')
    milestones = project.milestones.all().order_by('due_date')
    members = project.projectmember_set.select_related('user', 'user__role').all()
    files = project.files.filter(is_deleted=False).order_by('-uploaded_at')[:10]

    # Task status breakdown
    task_counts = project.get_task_counts()
    progress = project.get_progress()

    context = {
        'project': project,
        'tasks': tasks,
        'milestones': milestones,
        'members': members,
        'files': files,
        'task_counts': task_counts,
        'progress': progress,
        'all_users': User.objects.filter(is_active=True).exclude(id__in=[m.user.id for m in members]),
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_create_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()

            # Add creator / manager as member
            if project.manager:
                ProjectMember.objects.get_or_create(project=project, user=project.manager, defaults={'role': 'manager'})
            ProjectMember.objects.get_or_create(project=project, user=request.user, defaults={'role': 'manager'})

            log_activity(request.user, 'created', 'Projects', object_type='Project', object_id=project.id, object_repr=project.name, request=request)
            messages.success(request, f'Project "{project.name}" has been created successfully!')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectForm()

    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Create New Project'})


@login_required
def project_edit_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            log_activity(request.user, 'updated', 'Projects', object_type='Project', object_id=project.id, object_repr=project.name, request=request)
            messages.success(request, f'Project "{project.name}" has been updated!')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, 'projects/project_form.html', {'form': form, 'project': project, 'title': f'Edit {project.name}'})


@login_required
def project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        name = project.name
        log_activity(request.user, 'deleted', 'Projects', object_type='Project', object_id=project.id, object_repr=name, request=request)
        project.delete()
        messages.success(request, f'Project "{name}" was successfully deleted.')
        return redirect('projects:project_list')
    return render(request, 'projects/project_confirm_delete.html', {'project': project})


@login_required
def add_project_member_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role', 'member')
        user = get_object_or_404(User, id=user_id)
        ProjectMember.objects.get_or_create(project=project, user=user, defaults={'role': role})
        messages.success(request, f'{user.get_full_name()} was added to {project.name}.')
    return redirect('projects:project_detail', pk=project.pk)
