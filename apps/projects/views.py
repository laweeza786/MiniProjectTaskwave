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
    status_filter = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    department_filter = request.GET.get('department', '').strip()
    start_date_filter = request.GET.get('start_date', '').strip()
    end_date_filter = request.GET.get('end_date', '').strip()

    from apps.departments.models import Department
    departments = Department.objects.all().order_by('name')

    # Base query according to user role
    base_projects = Project.objects.select_related('department', 'manager').prefetch_related('members').all()
    if not (user.is_superuser or (user.role and user.role.name in ['Administrator', 'Project Manager'])):
        base_projects = base_projects.filter(Q(members=user) | Q(manager=user) | Q(visibility='organization')).distinct()

    # KPI counts from all accessible projects
    total_projects = base_projects.count()
    active_count = base_projects.filter(status__in=['active', 'in_progress']).count()
    completed_count = base_projects.filter(status='completed').count()
    on_hold_count = base_projects.filter(status='on_hold').count()

    # Apply filters
    projects = base_projects
    if query:
        projects = projects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(project_key__icontains=query) |
            Q(department__name__icontains=query)
        )
    if status_filter:
        if status_filter == 'active':
            projects = projects.filter(status__in=['active', 'in_progress'])
        else:
            projects = projects.filter(status=status_filter)
    if priority_filter:
        projects = projects.filter(priority=priority_filter)
    if department_filter:
        projects = projects.filter(department_id=department_filter)
    if start_date_filter:
        projects = projects.filter(start_date__gte=start_date_filter)
    if end_date_filter:
        projects = projects.filter(end_date__lte=end_date_filter)

    sample_projects = []
    icons = [
        ('ri-macbook-line', '#e0f2fe', '#0284c7'),
        ('ri-smartphone-line', '#fee2e2', '#ef4444'),
        ('ri-bank-line', '#f1f5f9', '#475569'),
        ('ri-tools-line', '#fef3c7', '#d97706'),
        ('ri-window-line', '#dcfce7', '#16a34a'),
    ]

    for idx, p in enumerate(projects):
        p_tasks = p.tasks.all()
        p_total = p_tasks.count()
        p_done = p_tasks.filter(status='completed').count()
        prog = int((p_done / p_total) * 100) if p_total > 0 else (p.get_progress() if hasattr(p, 'get_progress') else 0)
        icon, icon_bg, icon_color = icons[idx % len(icons)]

        sample_projects.append({
            'id': p.id,
            'name': p.name,
            'is_starred': getattr(p, 'is_starred', False),
            'subtitle': (p.description[:45] + '...') if p.description and len(p.description) > 45 else (p.description or 'Project deliverable'),
            'icon': icon,
            'icon_bg': icon_bg,
            'icon_color': icon_color,
            'progress': prog,
            'bar_color': '#22c55e' if prog >= 75 else ('#f59e0b' if prog >= 30 else '#94a3b8'),
            'status': p.get_status_display() if hasattr(p, 'get_status_display') else p.status.title(),
            'status_class': f"badge-{p.status.replace('_', '-')}",
            'department': p.department.name if p.department else 'General',
            'start_date': p.start_date.strftime('%d %b %Y') if p.start_date else 'Active',
            'end_date': p.end_date.strftime('%d %b %Y') if p.end_date else 'Ongoing',
            'date_range': f"{p.start_date.strftime('%d %b %Y') if p.start_date else 'Active'} - {p.end_date.strftime('%d %b %Y') if p.end_date else 'Ongoing'}",
            'avatars': ['img/avatars/rahul_kumar.jpg'],
            'extra_count': max(0, p.members.count() - 1)
        })
    context = {
        'projects': projects,
        'sample_projects': sample_projects,
        'total_projects': total_projects,
        'active_count': active_count,
        'completed_count': completed_count,
        'on_hold_count': on_hold_count,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'department_filter': department_filter,
        'start_date_filter': start_date_filter,
        'end_date_filter': end_date_filter,
        'departments': departments,
        'query': query,
        'is_manager_or_above': user.is_superuser or bool(user.role and user.role.name in ['Administrator', 'Project Manager']),
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
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied. Only Administrators and Project Managers can create projects.')
        return redirect('projects:project_list')

    from apps.departments.models import Department
    departments = Department.objects.all().order_by('name')
    team_members = User.objects.filter(is_active=True).select_related('department', 'role').order_by('first_name')

    if request.method == 'POST':
        post_data = request.POST.copy()

        # Clean department
        dept_val = post_data.get('department', '').strip()
        if dept_val and not dept_val.isdigit():
            # Check direct match
            d_obj = Department.objects.filter(name__iexact=dept_val).first()
            if not d_obj:
                # Check alias mapping
                dept_aliases = {
                    'development': 'Engineering',
                    'dev': 'Engineering',
                    'qa': 'Quality Assurance',
                    'design': 'UI/UX Design',
                    'marketing': 'Marketing & Sales',
                    'product': 'Product Management',
                }
                target_name = dept_aliases.get(dept_val.lower())
                if target_name:
                    d_obj = Department.objects.filter(name__iexact=target_name).first()
            if not d_obj:
                d_obj = Department.objects.filter(name__icontains=dept_val).first()
            if not d_obj:
                d_obj = Department.objects.first()

            if d_obj:
                post_data['department'] = d_obj.id

        # Clean dates
        for df in ['start_date', 'end_date']:
            val = post_data.get(df, '').strip()
            if val:
                for fmt in ('%Y-%m-%d', '%d %b %Y', '%d %B %Y', '%d/%m/%Y', '%m/%d/%Y'):
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(val, fmt)
                        post_data[df] = dt.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        pass

        # Clean priority
        prio_val = post_data.get('priority', '').lower()
        for p_opt in ['critical', 'high', 'medium', 'low']:
            if p_opt in prio_val:
                post_data['priority'] = p_opt
                break

        # Clean status
        stat_val = post_data.get('status', '').lower()
        for s_opt in ['planning', 'active', 'on_hold', 'completed', 'archived']:
            if s_opt.replace('_', ' ') in stat_val or s_opt in stat_val:
                post_data['status'] = s_opt
                break

        # Clean category
        cat_val = post_data.get('category', '').lower()
        if 'mobile' in cat_val:
            post_data['category'] = 'mobile_app'
        elif 'web' in cat_val:
            post_data['category'] = 'web_application'
        elif 'api' in cat_val:
            post_data['category'] = 'api'
        elif 'design' in cat_val:
            post_data['category'] = 'design'
        elif 'research' in cat_val:
            post_data['category'] = 'research'
        elif not post_data.get('category'):
            post_data['category'] = 'other'

        # Clean visibility
        vis_val = post_data.get('visibility', '').lower()
        if 'member' in vis_val:
            post_data['visibility'] = 'project_members'
        elif 'dep' in vis_val:
            post_data['visibility'] = 'department'
        elif 'org' in vis_val or 'public' in vis_val:
            post_data['visibility'] = 'organization'

        # Ensure project key uniqueness
        pkey = post_data.get('project_key', '').strip()
        if pkey:
            if Project.objects.filter(project_key=pkey).exists():
                import random
                post_data['project_key'] = f"{pkey}-{random.randint(10, 99)}"
        else:
            pname = post_data.get('name', 'TW')
            words = pname.split()
            key_slug = ''.join([w[0].upper() for w in words[:3]]) or 'PRJ'
            import random
            post_data['project_key'] = f"TW-{key_slug}{random.randint(10, 99)}"

        form = ProjectForm(post_data)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            if not project.manager:
                project.manager = request.user
            project.save()

            # Add selected members
            member_ids = request.POST.getlist('members')
            for mid in member_ids:
                try:
                    m_user = User.objects.get(id=mid)
                    ProjectMember.objects.get_or_create(project=project, user=m_user, defaults={'role': 'member'})
                except (User.DoesNotExist, ValueError):
                    pass

            # Always add manager and creator as members
            if project.manager:
                ProjectMember.objects.get_or_create(project=project, user=project.manager, defaults={'role': 'manager'})
            ProjectMember.objects.get_or_create(project=project, user=request.user, defaults={'role': 'manager'})

            # Save any milestones submitted
            milestone_titles = request.POST.getlist('milestone_titles[]')
            milestone_dates = request.POST.getlist('milestone_dates[]')
            from apps.projects.models import ProjectMilestone
            from datetime import datetime
            for m_title, m_date in zip(milestone_titles, milestone_dates):
                m_title = m_title.strip()
                if m_title:
                    m_due = None
                    if m_date:
                        for fmt in ('%Y-%m-%d', '%d %b %Y', '%d %B %Y'):
                            try:
                                m_due = datetime.strptime(m_date.strip(), fmt).date()
                                break
                            except ValueError:
                                pass
                    ProjectMilestone.objects.create(project=project, title=m_title, due_date=m_due)

            log_activity(request.user, 'created', 'Projects', object_type='Project', object_id=project.id, object_repr=project.name, request=request)
            messages.success(request, f'Project "{project.name}" has been created successfully!')
            return redirect('projects:project_detail', pk=project.pk)
        else:
            error_list = [f"{field}: {', '.join(errs)}" for field, errs in form.errors.items()]
            messages.error(request, f"Please correct the errors: {'; '.join(error_list)}")
    else:
        # Prepopulate with attractive defaults matching design
        initial_dept = Department.objects.first()
        form = ProjectForm(initial={
            'name': 'TaskWave Mobile App Development',
            'description': 'Develop a mobile application for TaskWave with core features including task management, notifications, team collaboration, and real-time updates.',
            'department': initial_dept.id if initial_dept else None,
            'category': 'mobile_app',
            'project_key': 'TW-MOB2',
            'priority': 'high',
            'status': 'active',
            'visibility': 'project_members',
            'client': 'Internal Use',
            'start_date': '2026-10-12',
            'end_date': '2026-12-30',
        })

    context = {
        'form': form,
        'title': 'Create New Project',
        'departments': departments,
        'team_members': team_members,
    }
    return render(request, 'projects/project_form.html', context)


@login_required
def project_edit_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator') or project.manager == request.user or project.created_by == request.user):
        messages.error(request, 'Permission denied. You cannot edit this project.')
        return redirect('projects:project_detail', pk=project.pk)

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
    if not (request.user.is_superuser or (request.user.role and request.user.role.name == 'Administrator') or project.manager == request.user):
        messages.error(request, 'Permission denied. You cannot delete this project.')
        return redirect('projects:project_detail', pk=project.pk)

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
