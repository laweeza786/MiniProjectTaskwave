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
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    project_filter = request.GET.get('project', '')
    assignee_filter = request.GET.get('assignee', '')
    my_tasks = request.GET.get('my_tasks', '')

    tasks = Task.objects.select_related('project', 'department', 'category', 'created_by').prefetch_related('assignees').all()

    # Filter by user if requested or if employee only
    if my_tasks or not (user.is_superuser or (user.role and user.role.name in ['Administrator', 'Project Manager'])):
        tasks = tasks.filter(Q(assignees=user) | Q(created_by=user)).distinct()

    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(task_number__icontains=query))
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if project_filter:
        tasks = tasks.filter(project_id=project_filter)
    if assignee_filter:
        tasks = tasks.filter(assignees__id=assignee_filter)

    total_tasks = 128
    in_progress_count = 42
    completed_count = 64
    overdue_count = 12

    sample_tasks = [
        {
            'id': 1,
            'title': 'Design User Interface',
            'subtitle': 'Create modern UI for dashboard',
            'project': 'TaskWave',
            'assignee': 'Rahul Kumar',
            'assignee_initials': 'RK',
            'assignee_avatar': 'img/avatars/rahul_kumar.jpg',
            'priority': 'High',
            'priority_class': 'badge-high',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'due_date': '2 Oct 2026',
            'progress': 60,
            'bar_color': '#f59e0b',
            'icon_class': 'ri-edit-circle-line',
            'icon_bg': '#fee2e2',
            'icon_color': '#ef4444'
        },
        {
            'id': 2,
            'title': 'Database Schema Design',
            'subtitle': 'Design database structure and relations',
            'project': 'College Portal',
            'assignee': 'Priya Singh',
            'assignee_initials': 'PS',
            'assignee_avatar': 'img/avatars/priya_singh.jpg',
            'priority': 'Medium',
            'priority_class': 'badge-medium',
            'status': 'Completed',
            'status_class': 'badge-completed',
            'due_date': '28 Sep 2026',
            'progress': 100,
            'bar_color': '#22c55e',
            'icon_class': 'ri-play-circle-line',
            'icon_bg': '#fef3c7',
            'icon_color': '#d97706'
        },
        {
            'id': 3,
            'title': 'API Development',
            'subtitle': 'Develop and test REST APIs',
            'project': 'Mobile App',
            'assignee': 'Aman Sharma',
            'assignee_initials': 'AS',
            'assignee_avatar': 'img/avatars/aman_sharma.jpg',
            'priority': 'High',
            'priority_class': 'badge-high',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'due_date': '5 Oct 2026',
            'progress': 50,
            'bar_color': '#f59e0b',
            'icon_class': 'ri-code-box-line',
            'icon_bg': '#e0f2fe',
            'icon_color': '#0284c7'
        },
        {
            'id': 4,
            'title': 'Testing & Bug Fixes',
            'subtitle': 'Fix reported issues and testing',
            'project': 'TaskWave',
            'assignee': 'Neha Tiwari',
            'assignee_initials': 'NT',
            'assignee_avatar': 'img/avatars/neha_tiwari.jpg',
            'priority': 'Medium',
            'priority_class': 'badge-medium',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'due_date': '3 Oct 2026',
            'progress': 40,
            'bar_color': '#f59e0b',
            'icon_class': 'ri-focus-3-line',
            'icon_bg': '#fee2e2',
            'icon_color': '#ef4444'
        },
        {
            'id': 5,
            'title': 'Project Documentation',
            'subtitle': 'Write technical documentation',
            'project': 'Website Redesign',
            'assignee': 'Vikram Singh',
            'assignee_initials': 'VS',
            'assignee_avatar': 'img/avatars/vikram_singh.jpg',
            'priority': 'Low',
            'priority_class': 'badge-low',
            'status': 'Not Started',
            'status_class': 'badge-not-started',
            'due_date': '10 Oct 2026',
            'progress': 0,
            'bar_color': '#cbd5e1',
            'icon_class': 'ri-file-text-line',
            'icon_bg': '#dcfce7',
            'icon_color': '#16a34a'
        },
        {
            'id': 6,
            'title': 'Client Review Meeting',
            'subtitle': 'Discuss progress with client',
            'project': 'College Portal',
            'assignee': 'Rahul Kumar',
            'assignee_initials': 'RK',
            'assignee_avatar': 'img/avatars/rahul_kumar.jpg',
            'priority': 'Medium',
            'priority_class': 'badge-medium',
            'status': 'Completed',
            'status_class': 'badge-completed',
            'due_date': '25 Sep 2026',
            'progress': 100,
            'bar_color': '#22c55e',
            'icon_class': 'ri-compass-3-line',
            'icon_bg': '#fef3c7',
            'icon_color': '#d97706'
        },
        {
            'id': 7,
            'title': 'UI Improvements',
            'subtitle': 'Enhance responsive design',
            'project': 'Mobile App',
            'assignee': 'Priya Singh',
            'assignee_initials': 'PS',
            'assignee_avatar': 'img/avatars/priya_singh.jpg',
            'priority': 'High',
            'priority_class': 'badge-high',
            'status': 'Overdue',
            'status_class': 'badge-overdue',
            'due_date': '20 Sep 2026',
            'progress': 20,
            'bar_color': '#ef4444',
            'icon_class': 'ri-compass-3-line',
            'icon_bg': '#fef3c7',
            'icon_color': '#d97706'
        },
        {
            'id': 8,
            'title': 'Deployment Setup',
            'subtitle': 'Setup server and deployment',
            'project': 'TaskWave',
            'assignee': 'Aman Sharma',
            'assignee_initials': 'AS',
            'assignee_avatar': 'img/avatars/aman_sharma.jpg',
            'priority': 'Medium',
            'priority_class': 'badge-medium',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'due_date': '6 Oct 2026',
            'progress': 70,
            'bar_color': '#f59e0b',
            'icon_class': 'ri-terminal-box-line',
            'icon_bg': '#e0f2fe',
            'icon_color': '#0284c7'
        },
        {
            'id': 9,
            'title': 'Performance Optimization',
            'subtitle': 'Improve application performance',
            'project': 'Database Optimization',
            'assignee': 'Neha Tiwari',
            'assignee_initials': 'NT',
            'assignee_avatar': 'img/avatars/neha_tiwari.jpg',
            'priority': 'Low',
            'priority_class': 'badge-low',
            'status': 'Not Started',
            'status_class': 'badge-not-started',
            'due_date': '12 Oct 2026',
            'progress': 0,
            'bar_color': '#cbd5e1',
            'icon_class': 'ri-compass-3-line',
            'icon_bg': '#fef3c7',
            'icon_color': '#d97706'
        },
        {
            'id': 10,
            'title': 'Security Testing',
            'subtitle': 'Perform security and vulnerability test',
            'project': 'Internal Tools',
            'assignee': 'Vikram Singh',
            'assignee_initials': 'VS',
            'assignee_avatar': 'img/avatars/vikram_singh.jpg',
            'priority': 'High',
            'priority_class': 'badge-high',
            'status': 'In Progress',
            'status_class': 'badge-in-progress',
            'due_date': '8 Oct 2026',
            'progress': 30,
            'bar_color': '#ef4444',
            'icon_class': 'ri-shield-check-line',
            'icon_bg': '#fee2e2',
            'icon_color': '#ef4444'
        },
        {
            'id': 11,
            'title': 'Content Update',
            'subtitle': 'Update website content and images',
            'project': 'Website Redesign',
            'assignee': 'Rahul Kumar',
            'assignee_initials': 'RK',
            'assignee_avatar': 'img/avatars/rahul_kumar.jpg',
            'priority': 'Low',
            'priority_class': 'badge-low',
            'status': 'Completed',
            'status_class': 'badge-completed',
            'due_date': '22 Sep 2026',
            'progress': 100,
            'bar_color': '#22c55e',
            'icon_class': 'ri-file-edit-line',
            'icon_bg': '#dcfce7',
            'icon_color': '#16a34a'
        },
        {
            'id': 12,
            'title': 'Final Review & Submission',
            'subtitle': 'Final check and submit project',
            'project': 'College Portal',
            'assignee': 'Priya Singh',
            'assignee_initials': 'PS',
            'assignee_avatar': 'img/avatars/priya_singh.jpg',
            'priority': 'Medium',
            'priority_class': 'badge-medium',
            'status': 'Not Started',
            'status_class': 'badge-not-started',
            'due_date': '15 Oct 2026',
            'progress': 0,
            'bar_color': '#cbd5e1',
            'icon_class': 'ri-compass-discover-line',
            'icon_bg': '#e0f2fe',
            'icon_color': '#0284c7'
        }
    ]

    projects = Project.objects.all().order_by('name')
    users = User.objects.filter(is_active=True).order_by('first_name')

    context = {
        'tasks': tasks,
        'sample_tasks': sample_tasks,
        'total_tasks': total_tasks,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'overdue_count': overdue_count,
        'projects': projects,
        'users': users,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'project_filter': project_filter,
        'query': query,
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
    project_id = request.GET.get('project', '')

    columns = [
        {
            'id': 'todo',
            'title': 'To Do',
            'dot_color': '#94a3b8',
            'count': 8,
            'tasks': [
                {
                    'title': 'Design Landing Page',
                    'desc': 'Create modern and responsive landing page for TaskWave.',
                    'tags': ['TaskWave', 'Design'],
                    'priority': 'High',
                    'priority_class': 'badge-high',
                    'date': '5 Oct 2026',
                    'avatars': ['RK', 'PS'],
                    'extra': 2
                },
                {
                    'title': 'Setup Development Environment',
                    'desc': 'Configure tools, libraries and project structure.',
                    'tags': ['Internal Tools', 'Setup'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '8 Oct 2026',
                    'avatars': ['NT'],
                    'extra': 0
                },
                {
                    'title': 'Create API Documentation',
                    'desc': 'Write complete API documentation for developers.',
                    'tags': ['Mobile App', 'Documentation'],
                    'priority': 'Low',
                    'priority_class': 'badge-low',
                    'date': '12 Oct 2026',
                    'avatars': ['AS', 'VS'],
                    'extra': 1
                },
                {
                    'title': 'UI Improvements',
                    'desc': 'Enhance dashboard UI based on feedback.',
                    'tags': ['TaskWave', 'Design'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '15 Oct 2026',
                    'avatars': ['PS', 'RK'],
                    'extra': 0
                },
                {
                    'title': 'Content Update',
                    'desc': 'Update website content and images.',
                    'tags': ['Website Redesign', 'Content'],
                    'priority': 'Low',
                    'priority_class': 'badge-low',
                    'date': '20 Oct 2026',
                    'avatars': ['SK'],
                    'extra': 0
                }
            ]
        },
        {
            'id': 'in_progress',
            'title': 'In Progress',
            'dot_color': '#f59e0b',
            'count': 6,
            'tasks': [
                {
                    'title': 'Database Schema Design',
                    'desc': 'Design database structure and relations.',
                    'tags': ['College Portal', 'Backend'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '28 Sep 2026',
                    'avatars': ['PS'],
                    'extra': 0
                },
                {
                    'title': 'API Development',
                    'desc': 'Develop and test REST APIs.',
                    'tags': ['Mobile App', 'Development'],
                    'priority': 'High',
                    'priority_class': 'badge-high',
                    'date': '5 Oct 2026',
                    'avatars': ['AS', 'RK'],
                    'extra': 1
                },
                {
                    'title': 'Testing & Bug Fixes',
                    'desc': 'Fix reported issues and perform testing.',
                    'tags': ['TaskWave', 'Testing'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '3 Oct 2026',
                    'avatars': ['NT'],
                    'extra': 0
                },
                {
                    'title': 'Deployment Setup',
                    'desc': 'Setup server and deployment.',
                    'tags': ['TaskWave', 'DevOps'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '6 Oct 2026',
                    'avatars': ['AS', 'VS'],
                    'extra': 0
                },
                {
                    'title': 'Performance Optimization',
                    'desc': 'Improve application performance.',
                    'tags': ['Database Optimization', 'Optimization'],
                    'priority': 'Low',
                    'priority_class': 'badge-low',
                    'date': '12 Oct 2026',
                    'avatars': ['NT'],
                    'extra': 0
                }
            ]
        },
        {
            'id': 'review',
            'title': 'Review',
            'dot_color': '#3b82f6',
            'count': 4,
            'tasks': [
                {
                    'title': 'Client Review Meeting',
                    'desc': 'Discuss progress with client.',
                    'tags': ['College Portal', 'Meeting'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '25 Sep 2026',
                    'avatars': ['RK', 'PS'],
                    'extra': 2
                },
                {
                    'title': 'Security Testing',
                    'desc': 'Perform security and vulnerability test.',
                    'tags': ['Internal Tools', 'Testing'],
                    'priority': 'High',
                    'priority_class': 'badge-high',
                    'date': '8 Oct 2026',
                    'avatars': ['VS'],
                    'extra': 0
                },
                {
                    'title': 'Final Review & Submission',
                    'desc': 'Final check and submit project.',
                    'tags': ['College Portal', 'Review'],
                    'priority': 'Medium',
                    'priority_class': 'badge-medium',
                    'date': '15 Oct 2026',
                    'avatars': ['PS'],
                    'extra': 0
                },
                {
                    'title': 'Mobile App Testing',
                    'desc': 'Test application on different devices.',
                    'tags': ['Mobile App', 'Testing'],
                    'priority': 'Low',
                    'priority_class': 'badge-low',
                    'date': '18 Oct 2026',
                    'avatars': ['AS', 'NT'],
                    'extra': 0
                }
            ]
        },
        {
            'id': 'completed',
            'title': 'Completed',
            'dot_color': '#22c55e',
            'count': 6,
            'tasks': [
                {
                    'title': 'Project Planning',
                    'desc': 'Define project scope and requirements.',
                    'tags': ['TaskWave', 'Planning'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '10 Sep 2026',
                    'avatars': ['RK', 'VS'],
                    'extra': 0
                },
                {
                    'title': 'Requirement Analysis',
                    'desc': 'Gather and analyze requirements.',
                    'tags': ['College Portal', 'Analysis'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '15 Sep 2026',
                    'avatars': ['PS'],
                    'extra': 0
                },
                {
                    'title': 'Wireframe Design',
                    'desc': 'Create wireframes for main pages.',
                    'tags': ['TaskWave', 'Design'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '20 Sep 2026',
                    'avatars': ['AS', 'NT'],
                    'extra': 2
                },
                {
                    'title': 'Authentication Module',
                    'desc': 'Implement login and registration.',
                    'tags': ['Internal Tools', 'Development'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '22 Sep 2026',
                    'avatars': ['VS'],
                    'extra': 0
                },
                {
                    'title': 'Dashboard Module',
                    'desc': 'Develop admin dashboard.',
                    'tags': ['TaskWave', 'Development'],
                    'priority': 'Completed',
                    'priority_class': 'badge-completed',
                    'date': '25 Sep 2026',
                    'avatars': ['RK', 'PS'],
                    'extra': 1
                }
            ]
        }
    ]

    avatar_map = {
        'RK': 'img/avatars/rahul_kumar.jpg',
        'PS': 'img/avatars/priya_singh.jpg',
        'AS': 'img/avatars/aman_sharma.jpg',
        'NT': 'img/avatars/neha_tiwari.jpg',
        'VS': 'img/avatars/vikram_singh.jpg',
        'SK': 'img/avatars/sahil_khan.jpg',
    }
    for col in columns:
        for t in col['tasks']:
            t['avatars'] = [avatar_map.get(a, 'img/avatars/rahul_kumar.jpg') for a in t['avatars']]

    context = {
        'columns': columns,
        'selected_project': project_id,
    }
    return render(request, 'tasks/kanban_board.html', context)
