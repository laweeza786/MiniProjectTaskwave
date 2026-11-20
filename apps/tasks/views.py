from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse

from apps.tasks.models import (
    Task, TaskAssignee, Subtask, TaskComment, TaskAttachment,
    TaskSubmission, TaskSubmissionFile, TaskReview, TaskStatusHistory, TaskCategory
)
from apps.tasks.forms import TaskForm, SubtaskForm, TaskCommentForm, TaskSubmissionForm, TaskReviewForm
from apps.projects.models import Project
from apps.users.models import User
from apps.audit.middleware import log_activity


@login_required
def task_list_view(request):
    user = request.user
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    project_filter = request.GET.get('project', '').strip()
    assignee_filter = request.GET.get('assignee', '').strip()
    my_tasks = request.GET.get('my_tasks', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    base_tasks = Task.objects.select_related('project', 'department', 'category', 'created_by').prefetch_related('assignees').all()

    # Dynamic KPI counts
    total_tasks = base_tasks.count()
    my_tasks_count = base_tasks.filter(assignees=user).distinct().count()
    in_progress_count = base_tasks.filter(status='in_progress').count()
    completed_count = base_tasks.filter(status='completed').count()
    overdue_count = base_tasks.filter(
        Q(status='overdue') | Q(due_date__lt=timezone.now().date(), status__in=['assigned', 'in_progress', 'under_review'])
    ).count()

    tasks_qs = base_tasks

    # Filter by user if requested
    if my_tasks in ['true', '1', True]:
        tasks_qs = tasks_qs.filter(assignees=user).distinct()

    if query:
        tasks_qs = tasks_qs.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(task_number__icontains=query) | Q(project__name__icontains=query)
        )

    if status_filter:
        s_norm = status_filter.lower().replace('-', '_').replace(' ', '_').strip()
        if s_norm == 'in_progress':
            tasks_qs = tasks_qs.filter(status='in_progress')
        elif s_norm in ['completed', 'overdue', 'under_review', 'assigned', 'draft', 'cancelled']:
            tasks_qs = tasks_qs.filter(status=s_norm)
        else:
            tasks_qs = tasks_qs.filter(status__icontains=status_filter)

    if priority_filter:
        tasks_qs = tasks_qs.filter(priority=priority_filter.lower())

    if project_filter:
        if project_filter.isdigit():
            tasks_qs = tasks_qs.filter(project_id=int(project_filter))
        else:
            tasks_qs = tasks_qs.filter(project__name__icontains=project_filter)

    if assignee_filter:
        if assignee_filter.isdigit():
            tasks_qs = tasks_qs.filter(assignees__id=int(assignee_filter))
        else:
            tasks_qs = tasks_qs.filter(Q(assignees__first_name__icontains=assignee_filter) | Q(assignees__last_name__icontains=assignee_filter))

    if start_date:
        tasks_qs = tasks_qs.filter(due_date__gte=start_date)

    if end_date:
        tasks_qs = tasks_qs.filter(due_date__lte=end_date)

    tasks_qs = tasks_qs.order_by('-created_at')

    # Format tasks for template
    formatted_tasks = []
    for t in tasks_qs:
        first_assignee = t.assignees.first()
        assignee_avatar = first_assignee.profile_picture.url if first_assignee and first_assignee.profile_picture else ''
        assignee_initials = (first_assignee.first_name[:1] + first_assignee.last_name[:1]) if first_assignee and first_assignee.first_name else 'NA'
        assignee_name = first_assignee.get_full_name() or first_assignee.email if first_assignee else 'Unassigned'

        prio_display = t.get_priority_display() if hasattr(t, 'get_priority_display') else t.priority.title()
        prio_class = 'badge-high' if t.priority in ['high', 'critical'] else ('badge-medium' if t.priority == 'medium' else 'badge-low')

        status_display = t.get_status_display() if hasattr(t, 'get_status_display') else t.status.replace('_', ' ').title()
        if t.status == 'completed':
            status_class = 'badge-completed'
        elif t.status == 'in_progress':
            status_class = 'badge-in-progress'
        elif t.status == 'overdue':
            status_class = 'badge-overdue'
        elif t.status == 'under_review':
            status_class = 'badge-review'
        else:
            status_class = 'badge-assigned'

        prog = t.progress or 0
        bar_color = '#22c55e' if prog >= 75 else ('#f59e0b' if prog >= 30 else '#cbd5e1')

        if t.status == 'completed':
            icon_class = 'ri-checkbox-circle-line'
            icon_bg = '#dcfce7'
            icon_color = '#16a34a'
        elif t.status == 'in_progress':
            icon_class = 'ri-play-circle-line'
            icon_bg = '#fef3c7'
            icon_color = '#d97706'
        elif t.status == 'under_review':
            icon_class = 'ri-eye-line'
            icon_bg = '#ede9fe'
            icon_color = '#7c3aed'
        else:
            icon_class = 'ri-file-text-line'
            icon_bg = '#e0f2fe'
            icon_color = '#0284c7'

        formatted_tasks.append({
            'id': t.id,
            'task_number': t.task_number,
            'title': t.title,
            'subtitle': (t.description[:45] + '...') if t.description and len(t.description) > 45 else (t.description or 'No description'),
            'project': t.project.name if t.project else 'General',
            'project_id': t.project_id,
            'assignees': list(t.assignees.all()),
            'assignee': assignee_name,
            'assignee_initials': assignee_initials,
            'assignee_avatar': assignee_avatar,
            'priority': prio_display,
            'priority_class': prio_class,
            'status': status_display,
            'status_class': status_class,
            'due_date': t.due_date.strftime('%d %b %Y') if t.due_date else 'No Due Date',
            'progress': prog,
            'bar_color': bar_color,
            'icon_class': icon_class,
            'icon_bg': icon_bg,
            'icon_color': icon_color,
        })

    from django.core.paginator import Paginator
    try:
        per_page = int(request.GET.get('per_page', 10))
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(formatted_tasks, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    projects = Project.objects.all().order_by('name')
    users = User.objects.filter(is_active=True).order_by('first_name')

    is_lead_or_above = user.is_superuser or bool(user.role and user.role.name in ['Administrator', 'Project Manager', 'Team Lead'])

    context = {
        'tasks': page_obj,
        'page_obj': page_obj,
        'sample_tasks': page_obj,
        'total_tasks': total_tasks,
        'my_tasks_count': my_tasks_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'overdue_count': overdue_count,
        'projects': projects,
        'users': users,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'project_filter': project_filter,
        'assignee_filter': assignee_filter,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
        'my_tasks': my_tasks,
        'per_page': per_page,
        'is_lead_or_above': is_lead_or_above,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(
        Task.objects.select_related('project', 'department', 'category', 'created_by')
        .prefetch_related('assignees', 'subtasks', 'comments__user', 'attachments', 'submissions__files'),
        pk=pk
    )
    comments = task.comments.all().order_by('created_at')
    subtasks = task.subtasks.all().order_by('order', 'created_at')
    attachments = task.attachments.all().order_by('-uploaded_at')
    submissions = task.submissions.all().order_by('-submitted_at')
    status_history = task.status_history.all().order_by('-changed_at')

    comment_form = TaskCommentForm()
    subtask_form = SubtaskForm()
    submission_form = TaskSubmissionForm()
    review_form = TaskReviewForm()

    all_users = User.objects.filter(is_active=True).exclude(id__in=[a.id for a in task.assignees.all()])

    context = {
        'task': task,
        'comments': comments,
        'subtasks': subtasks,
        'attachments': attachments,
        'submissions': submissions,
        'status_history': status_history,
        'comment_form': comment_form,
        'subtask_form': subtask_form,
        'submission_form': submission_form,
        'review_form': review_form,
        'all_users': all_users,
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_create_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager', 'Team Lead'])):
        messages.error(request, 'Permission denied. Only Administrators, Project Managers, and Team Leads can create and assign tasks.')
        return redirect('tasks:task_list')

    if request.method == 'POST':

        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()

            # Handle assignees
            assignee_ids = request.POST.getlist('assignees')
            for uid in assignee_ids:
                user = User.objects.filter(id=uid).first()
                if user:
                    TaskAssignee.objects.create(task=task, user=user, assigned_by=request.user)

            # Record status history
            TaskStatusHistory.objects.create(
                task=task,
                from_status='',
                to_status=task.status,
                changed_by=request.user,
                reason='Task created'
            )

            log_activity(request.user, 'created', 'Tasks', object_type='Task', object_id=task.id, object_repr=task.title, request=request)
            messages.success(request, f'Task "{task.title}" has been created!')
            return redirect('tasks:task_detail', pk=task.pk)
    else:
        initial = {}
        project_id = request.GET.get('project')
        if project_id:
            initial['project'] = project_id
        form = TaskForm(initial=initial)

    users = User.objects.filter(is_active=True)
    return render(request, 'tasks/task_form.html', {'form': form, 'users': users, 'title': 'Create New Task'})


@login_required
def task_edit_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager', 'Team Lead']) or task.created_by == request.user):
        messages.error(request, 'Permission denied. You do not have permission to edit this task configuration.')
        return redirect('tasks:task_detail', pk=task.pk)

    old_status = task.status


    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()

            if old_status != updated_task.status:
                TaskStatusHistory.objects.create(
                    task=updated_task,
                    from_status=old_status,
                    to_status=updated_task.status,
                    changed_by=request.user,
                    reason='Status updated during task edit'
                )

            # Update assignees
            new_assignee_ids = set(map(int, request.POST.getlist('assignees')))
            current_assignee_ids = set(task.assignees.values_list('id', flat=True))

            to_add = new_assignee_ids - current_assignee_ids
            to_remove = current_assignee_ids - new_assignee_ids

            for uid in to_add:
                u = User.objects.filter(id=uid).first()
                if u:
                    TaskAssignee.objects.create(task=task, user=u, assigned_by=request.user)

            TaskAssignee.objects.filter(task=task, user_id__in=to_remove).delete()

            log_activity(request.user, 'updated', 'Tasks', object_type='Task', object_id=task.id, object_repr=task.title, request=request)
            messages.success(request, f'Task "{task.title}" updated!')
            return redirect('tasks:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)

    users = User.objects.filter(is_active=True)
    current_assignee_ids = list(task.assignees.values_list('id', flat=True))
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'task': task,
        'is_edit': True,
        'users': users,
        'current_assignee_ids': current_assignee_ids,
        'title': f'Edit Task: {task.title}'
    })


@login_required
def task_delete_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager', 'Team Lead']) or task.created_by == request.user):
        messages.error(request, 'Permission denied. Only Administrators, Project Managers, and Team Leads can delete tasks.')
        return redirect('tasks:task_detail', pk=task.pk)

    if request.method == 'POST':

        title = task.title
        log_activity(request.user, 'deleted', 'Tasks', object_type='Task', object_id=task.id, object_repr=title, request=request)
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('tasks:task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def add_task_comment_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            log_activity(request.user, 'created', 'Tasks', object_type='TaskComment', object_id=comment.id, object_repr=f'Comment on {task.title}', request=request)
            messages.success(request, 'Comment added.')
    return redirect('tasks:task_detail', pk=task.pk)


@login_required
def add_subtask_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = SubtaskForm(request.POST)
        if form.is_valid():
            subtask = form.save(commit=False)
            subtask.task = task
            subtask.save()
            messages.success(request, 'Subtask added.')
    return redirect('tasks:task_detail', pk=task.pk)


@login_required
def submit_task_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.task = task
            submission.submitted_by = request.user
            submission.version = task.submissions.count() + 1
            submission.status = 'pending'
            submission.save()

            # Handle file uploads if any
            files = request.FILES.getlist('submission_files')
            for f in files:
                TaskSubmissionFile.objects.create(
                    submission=submission,
                    file=f,
                    original_filename=f.name,
                    file_size=f.size
                )

            # Update task status to submitted
            old_status = task.status
            task.status = 'submitted'
            task.save()

            TaskStatusHistory.objects.create(
                task=task,
                from_status=old_status,
                to_status='submitted',
                changed_by=request.user,
                reason='Submitted for review'
            )

            log_activity(request.user, 'submitted', 'Tasks', object_type='TaskSubmission', object_id=submission.id, object_repr=f'Submission for {task.title}', request=request)
            messages.success(request, 'Work submitted for review!')
    return redirect('tasks:task_detail', pk=task.pk)


@login_required
def review_task_view(request, pk, submission_id):
    task = get_object_or_404(Task, pk=pk)
    submission = get_object_or_404(TaskSubmission, pk=submission_id, task=task)
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager', 'Team Lead']) or task.created_by == request.user):
        messages.error(request, 'Permission denied. Only Administrators, Managers, and Team Leads can review deliverables.')
        return redirect('tasks:task_detail', pk=task.pk)

    if request.method == 'POST':

        form = TaskReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.submission = submission
            review.reviewer = request.user
            review.save()

            decision = form.cleaned_data['decision']
            submission.status = decision
            submission.save()

            old_status = task.status
            if decision == 'approved':
                task.status = 'completed'
                task.progress = 100
                task.completed_at = timezone.now()
            elif decision == 'changes_requested':
                task.status = 'changes_requested'
            elif decision == 'rejected':
                task.status = 'in_progress'
            task.save()

            TaskStatusHistory.objects.create(
                task=task,
                from_status=old_status,
                to_status=task.status,
                changed_by=request.user,
                reason=f'Review decision: {decision}'
            )

            log_activity(request.user, decision, 'Tasks', object_type='TaskReview', object_id=review.id, object_repr=f'Review of {task.title}', request=request)
            messages.success(request, f'Review submitted: {decision.replace("_", " ").title()}!')
    return redirect('tasks:task_detail', pk=task.pk)


# Kanban board view
@login_required
def kanban_board_view(request):
    user = request.user
    project_filter = request.GET.get('project', '').strip()
    assignee_filter = request.GET.get('assignee', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    status_filter = request.GET.get('status', '').strip()
    query = request.GET.get('q', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    # Base columns structure
    columns = [
        {
            'id': 'todo',
            'status_value': 'assigned',
            'title': 'To Do',
            'dot_color': '#94a3b8',
            'tasks': [
                {
                    'id': 101,
                    'title': 'Design Landing Page',
                    'desc': 'Create modern and responsive landing page for TaskWave.',
                    'project': 'TaskWave',
                    'tags': ['TaskWave', 'Design'],
                    'priority': 'High',
                    'priority_class': 'badge-high',
                    'date': '5 Oct 2026',
                    'date_iso': '2026-10-05',
                    'assignee_names': 'Rahul Kumar, Priya Singh',
                    'avatars': ['img/avatars/rahul_kumar.jpg', 'img/avatars/priya_singh.jpg'],
                    'extra': 2,
                    'is_real': False
                },
                {
                    'id': 102,
                    'title': 'Setup Development Environment',
                    'desc': 'Configure tools, libraries and project structure.',
                    'project': 'Internal Tools',
                    'tags': ['Internal Tools', 'Setup'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '8 Oct 2026',
                    'date_iso': '2026-10-08',
                    'assignee_names': 'Neha Tiwari',
                    'avatars': ['img/avatars/neha_tiwari.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 103,
                    'title': 'Create API Documentation',
                    'desc': 'Write complete API documentation for developers.',
                    'project': 'Mobile App',
                    'tags': ['Mobile App', 'Documentation'],
                    'priority': 'Low',
                    'priority_class': 'badge-low',
                    'date': '12 Oct 2026',
                    'date_iso': '2026-10-12',
                    'assignee_names': 'Aman Sharma, Vikram Singh',
                    'avatars': ['img/avatars/aman_sharma.jpg', 'img/avatars/vikram_singh.jpg'],
                    'extra': 1,
                    'is_real': False
                },
                {
                    'id': 104,
                    'title': 'UI Improvements',
                    'desc': 'Enhance dashboard UI based on feedback.',
                    'project': 'TaskWave',
                    'tags': ['TaskWave', 'Design'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '15 Oct 2026',
                    'date_iso': '2026-10-15',
                    'assignee_names': 'Priya Singh, Rahul Kumar',
                    'avatars': ['img/avatars/priya_singh.jpg', 'img/avatars/rahul_kumar.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 105,
                    'title': 'Content Update',
                    'desc': 'Update website content and images.',
                    'project': 'Website Redesign',
                    'tags': ['Website Redesign', 'Content'],
                    'priority': 'Low',
                    'priority_class': 'badge-low',
                    'date': '20 Oct 2026',
                    'date_iso': '2026-10-20',
                    'assignee_names': 'Sahil Khan',
                    'avatars': ['img/avatars/sahil_khan.jpg'],
                    'extra': 0,
                    'is_real': False
                }
            ]
        },
        {
            'id': 'in_progress',
            'status_value': 'in_progress',
            'title': 'In Progress',
            'dot_color': '#f59e0b',
            'tasks': [
                {
                    'id': 106,
                    'title': 'Database Schema Design',
                    'desc': 'Design database structure and relations.',
                    'project': 'College Portal',
                    'tags': ['College Portal', 'Backend'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '28 Sep 2026',
                    'date_iso': '2026-09-28',
                    'assignee_names': 'Priya Singh',
                    'avatars': ['img/avatars/priya_singh.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 107,
                    'title': 'API Development',
                    'desc': 'Develop and test REST APIs.',
                    'project': 'Mobile App',
                    'tags': ['Mobile App', 'Development'],
                    'priority': 'High',
                    'priority_class': 'badge-high',
                    'date': '5 Oct 2026',
                    'date_iso': '2026-10-05',
                    'assignee_names': 'Aman Sharma, Rahul Kumar',
                    'avatars': ['img/avatars/aman_sharma.jpg', 'img/avatars/rahul_kumar.jpg'],
                    'extra': 1,
                    'is_real': False
                },
                {
                    'id': 108,
                    'title': 'Testing & Bug Fixes',
                    'desc': 'Fix reported issues and perform testing.',
                    'project': 'TaskWave',
                    'tags': ['TaskWave', 'Testing'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '3 Oct 2026',
                    'date_iso': '2026-10-03',
                    'assignee_names': 'Neha Tiwari',
                    'avatars': ['img/avatars/neha_tiwari.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 109,
                    'title': 'Deployment Setup',
                    'desc': 'Setup server and deployment.',
                    'project': 'TaskWave',
                    'tags': ['TaskWave', 'DevOps'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '6 Oct 2026',
                    'date_iso': '2026-10-06',
                    'assignee_names': 'Aman Sharma, Vikram Singh',
                    'avatars': ['img/avatars/aman_sharma.jpg', 'img/avatars/vikram_singh.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 110,
                    'title': 'Performance Optimization',
                    'desc': 'Improve application performance.',
                    'project': 'Database Optimization',
                    'tags': ['Database Optimization', 'Optimization'],
                    'priority': 'Low',
                    'priority_class': 'badge-low',
                    'date': '12 Oct 2026',
                    'date_iso': '2026-10-12',
                    'assignee_names': 'Neha Tiwari',
                    'avatars': ['img/avatars/neha_tiwari.jpg'],
                    'extra': 0,
                    'is_real': False
                }
            ]
        },
        {
            'id': 'review',
            'status_value': 'submitted',
            'title': 'Review',
            'dot_color': '#3b82f6',
            'tasks': [
                {
                    'id': 111,
                    'title': 'Client Review Meeting',
                    'desc': 'Discuss progress with client.',
                    'project': 'College Portal',
                    'tags': ['College Portal', 'Meeting'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '25 Sep 2026',
                    'date_iso': '2026-09-25',
                    'assignee_names': 'Rahul Kumar, Priya Singh',
                    'avatars': ['img/avatars/rahul_kumar.jpg', 'img/avatars/priya_singh.jpg'],
                    'extra': 2,
                    'is_real': False
                },
                {
                    'id': 112,
                    'title': 'Security Testing',
                    'desc': 'Perform security and vulnerability test.',
                    'project': 'Internal Tools',
                    'tags': ['Internal Tools', 'Testing'],
                    'priority': 'High',
                    'priority_class': 'badge-high',
                    'date': '8 Oct 2026',
                    'date_iso': '2026-10-08',
                    'assignee_names': 'Vikram Singh',
                    'avatars': ['img/avatars/vikram_singh.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 113,
                    'title': 'Final Review & Submission',
                    'desc': 'Final check and submit project.',
                    'project': 'College Portal',
                    'tags': ['College Portal', 'Review'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '15 Oct 2026',
                    'date_iso': '2026-10-15',
                    'assignee_names': 'Priya Singh',
                    'avatars': ['img/avatars/priya_singh.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 114,
                    'title': 'Mobile App Testing',
                    'desc': 'Test application on different devices.',
                    'project': 'Mobile App',
                    'tags': ['Mobile App', 'Testing'],
                    'priority': 'Low',
                    'priority_class': 'badge-low',
                    'date': '18 Oct 2026',
                    'date_iso': '2026-10-18',
                    'assignee_names': 'Aman Sharma, Neha Tiwari',
                    'avatars': ['img/avatars/aman_sharma.jpg', 'img/avatars/neha_tiwari.jpg'],
                    'extra': 0,
                    'is_real': False
                }
            ]
        },
        {
            'id': 'completed',
            'status_value': 'completed',
            'title': 'Completed',
            'dot_color': '#22c55e',
            'tasks': [
                {
                    'id': 115,
                    'title': 'Project Planning',
                    'desc': 'Define project scope and requirements.',
                    'project': 'TaskWave',
                    'tags': ['TaskWave', 'Planning'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '10 Sep 2026',
                    'date_iso': '2026-09-10',
                    'assignee_names': 'Rahul Kumar, Vikram Singh',
                    'avatars': ['img/avatars/rahul_kumar.jpg', 'img/avatars/vikram_singh.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 116,
                    'title': 'Requirement Analysis',
                    'desc': 'Gather and analyze requirements.',
                    'project': 'College Portal',
                    'tags': ['College Portal', 'Analysis'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '15 Sep 2026',
                    'date_iso': '2026-09-15',
                    'assignee_names': 'Priya Singh',
                    'avatars': ['img/avatars/priya_singh.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 117,
                    'title': 'Wireframe Design',
                    'desc': 'Create wireframes for main pages.',
                    'project': 'TaskWave',
                    'tags': ['TaskWave', 'Design'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '20 Sep 2026',
                    'date_iso': '2026-09-20',
                    'assignee_names': 'Aman Sharma, Neha Tiwari',
                    'avatars': ['img/avatars/aman_sharma.jpg', 'img/avatars/neha_tiwari.jpg'],
                    'extra': 2,
                    'is_real': False
                },
                {
                    'id': 118,
                    'title': 'Authentication Module',
                    'desc': 'Implement login and registration.',
                    'project': 'Internal Tools',
                    'tags': ['Internal Tools', 'Development'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '22 Sep 2026',
                    'date_iso': '2026-09-22',
                    'assignee_names': 'Vikram Singh',
                    'avatars': ['img/avatars/vikram_singh.jpg'],
                    'extra': 0,
                    'is_real': False
                },
                {
                    'id': 119,
                    'title': 'Dashboard Module',
                    'desc': 'Develop admin dashboard.',
                    'project': 'TaskWave',
                    'tags': ['TaskWave', 'Development'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '25 Sep 2026',
                    'date_iso': '2026-09-25',
                    'assignee_names': 'Rahul Kumar, Priya Singh',
                    'avatars': ['img/avatars/rahul_kumar.jpg', 'img/avatars/priya_singh.jpg'],
                    'extra': 1,
                    'is_real': False
                }
            ]
        }
    ]

    # Map real database tasks into columns
    status_to_col = {
        'assigned': 'todo',
        'todo': 'todo',
        'pending': 'todo',
        'not_started': 'todo',
        'in_progress': 'in_progress',
        'submitted': 'review',
        'changes_requested': 'review',
        'review': 'review',
        'completed': 'completed',
        'approved': 'completed',
    }
    col_map = {c['id']: c for c in columns}

    db_tasks = Task.objects.select_related('project').prefetch_related('assignees').all()
    for t in db_tasks:
        target_col_id = status_to_col.get(t.status, 'todo')
        assignees_list = list(t.assignees.all())
        avatars = []
        for a in assignees_list[:2]:
            if a.profile_picture:
                avatars.append(a.profile_picture.url)
            else:
                avatars.append('img/avatars/rahul_kumar.jpg')
        if not avatars:
            avatars = ['img/avatars/rahul_kumar.jpg']

        assignee_names = ', '.join([a.get_full_name() for a in assignees_list]) or 'Unassigned'
        proj_name = t.project.name if t.project else 'TaskWave'
        prio_title = t.get_priority_display() if hasattr(t, 'get_priority_display') else t.priority.capitalize()

        task_item = {
            'id': t.id,
            'title': t.title,
            'desc': (t.description[:70] + '...') if len(t.description) > 70 else (t.description or 'Task deliverable'),
            'project': proj_name,
            'tags': [proj_name, prio_title],
            'priority': prio_title,
            'priority_class': f"badge-{t.priority.lower()}",
            'date': t.due_date.strftime('%d %b %Y') if t.due_date else 'No deadline',
            'date_iso': t.due_date.strftime('%Y-%m-%d') if t.due_date else '',
            'assignee_names': assignee_names,
            'avatars': avatars,
            'extra': max(0, len(assignees_list) - 2),
            'is_real': True,
        }
        # Prepend real tasks to column
        if target_col_id in col_map:
            col_map[target_col_id]['tasks'].insert(0, task_item)

    # Calculate counts
    for col in columns:
        col['count'] = len(col['tasks'])

    # Aggregate all distinct projects and assignees for dropdowns
    project_set = set(['TaskWave', 'College Portal', 'Mobile App', 'Internal Tools', 'Website Redesign', 'Database Optimization'])
    for p in Project.objects.all():
        project_set.add(p.name)
    all_projects = sorted(list(project_set))

    assignee_set = set(['Rahul Kumar', 'Priya Singh', 'Aman Sharma', 'Neha Tiwari', 'Vikram Singh', 'Sahil Khan'])
    for u in User.objects.filter(is_active=True):
        assignee_set.add(u.get_full_name())
    all_assignees = sorted(list(assignee_set))

    context = {
        'columns': columns,
        'all_projects': all_projects,
        'all_assignees': all_assignees,
        'selected_project': project_filter,
        'selected_assignee': assignee_filter,
        'selected_priority': priority_filter,
        'selected_status': status_filter,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'tasks/kanban_board.html', context)
