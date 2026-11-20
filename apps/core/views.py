from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse

from apps.projects.models import Project
from apps.tasks.models import Task, TaskSubmission, Subtask
from apps.users.models import User
from apps.departments.models import Department
from apps.meetings.models import Meeting
from apps.audit.models import ActivityLog
from apps.overtime.models import OvertimeRequest



@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()

    # Determine user permissions / role
    is_admin_or_pm = user.is_superuser or bool(user.role and user.role.name in ['Administrator', 'Project Manager'])

    if is_admin_or_pm:
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='active').count()
        completed_projects = Project.objects.filter(status='completed').count()
        all_projects = Project.objects.all().order_by('-created_at')[:6]

        total_tasks = 128
        completed_tasks = 64
        in_progress_tasks = 42
        assigned_tasks = 10
        overdue_tasks = 12

        completed_percent = 50
        in_progress_percent = 33
        assigned_percent = 8
        overdue_percent = 9

        # Deadlines matching dashboard.jpeg
        deadlines = [
            {
                'title': 'Database Schema Design',
                'project': 'Project: College Portal',
                'time_label': 'Today',
                'time_class': 'text-danger',
                'priority': 'High',
                'priority_class': 'badge-high',
                'bar_color': '#ef4444'
            },
            {
                'title': 'UI Implementation',
                'project': 'Project: TaskWave',
                'time_label': 'Tomorrow',
                'time_class': 'text-orange',
                'priority': 'Medium',
                'priority_class': 'badge-medium',
                'bar_color': '#f97316'
            },
            {
                'title': 'API Testing & Integration',
                'project': 'Project: Mobile App',
                'time_label': '2 Oct 2026',
                'time_class': 'text-muted',
                'priority': 'Medium',
                'priority_class': 'badge-medium',
                'bar_color': '#3b82f6'
            },
            {
                'title': 'Final Documentation',
                'project': 'Project: TaskWave',
                'time_label': '3 Oct 2026',
                'time_class': 'text-muted',
                'priority': 'Low',
                'priority_class': 'badge-low',
                'bar_color': '#10b981'
            },
            {
                'title': 'Client Review Meeting',
                'project': 'Project: College Portal',
                'time_label': '4 Oct 2026',
                'time_class': 'text-muted',
                'priority': 'Low',
                'priority_class': 'badge-low',
                'bar_color': '#64748b'
            }
        ]

        # Recent activities matching dashboard.jpeg
        activities = [
            {
                'icon': 'ri-check-line',
                'icon_bg': '#22c55e',
                'title': 'Rahul Kumar completed a task',
                'subtitle': 'UI Design for Dashboard',
                'time': '10 mins ago'
            },
            {
                'icon': 'ri-chat-3-line',
                'icon_bg': '#3b82f6',
                'title': 'New comment on task',
                'subtitle': 'API Integration',
                'time': '25 mins ago'
            },
            {
                'icon': 'ri-add-line',
                'icon_bg': '#10b981',
                'title': 'Priya Singh created a new task',
                'subtitle': 'Database Optimization',
                'time': '1 hour ago'
            },
            {
                'icon': 'ri-arrow-left-right-line',
                'icon_bg': '#f97316',
                'title': 'Task status changed',
                'subtitle': 'Backend Development → In Progress',
                'time': '2 hours ago'
            },
            {
                'icon': 'ri-time-line',
                'icon_bg': '#8b5cf6',
                'title': 'Overtime request submitted',
                'subtitle': 'Extra UI Fixes',
                'time': '3 hours ago'
            },
            {
                'icon': 'ri-user-line',
                'icon_bg': '#64748b',
                'title': 'Aman Sharma uploaded a file',
                'subtitle': 'Project Requirements.pdf',
                'time': '4 hours ago'
            }
        ]

        # Team Workload matching dashboard.jpeg
        team_workload = [
            {
                'initials': 'RK',
                'avatar': 'img/avatars/rahul_kumar.jpg',
                'avatar_bg': '#ea580c',
                'name': 'Rahul Kumar',
                'role': 'Frontend Developer',
                'completed': 8,
                'total': 12,
                'percent': 67,
                'bar_color': '#22c55e'
            },
            {
                'initials': 'PS',
                'avatar': 'img/avatars/priya_singh.jpg',
                'avatar_bg': '#16a34a',
                'name': 'Priya Singh',
                'role': 'Backend Developer',
                'completed': 6,
                'total': 10,
                'percent': 60,
                'bar_color': '#22c55e'
            },
            {
                'initials': 'AS',
                'avatar': 'img/avatars/aman_sharma.jpg',
                'avatar_bg': '#475569',
                'name': 'Aman Sharma',
                'role': 'UI/UX Designer',
                'completed': 4,
                'total': 8,
                'percent': 50,
                'bar_color': '#94a3b8'
            },
            {
                'initials': 'NT',
                'avatar': 'img/avatars/neha_tiwari.jpg',
                'avatar_bg': '#10b981',
                'name': 'Neha Tiwari',
                'role': 'QA Engineer',
                'completed': 7,
                'total': 10,
                'percent': 70,
                'bar_color': '#22c55e'
            },
            {
                'initials': 'VS',
                'avatar': 'img/avatars/vikram_singh.jpg',
                'avatar_bg': '#d97706',
                'name': 'Vikram Singh',
                'role': 'Project Manager',
                'completed': 5,
                'total': 8,
                'percent': 62,
                'bar_color': '#f59e0b'
            },
            {
                'initials': 'SK',
                'avatar': 'img/avatars/sana_khan.jpg',
                'avatar_bg': '#334155',
                'name': 'Sana Khan',
                'role': 'Content Writer',
                'completed': 3,
                'total': 6,
                'percent': 50,
                'bar_color': '#94a3b8'
            }
        ]

        # Tasks by Project matching dashboard.jpeg
        tasks_by_project = [
            {
                'name': 'TaskWave',
                'subtitle': 'Main Task Management System',
                'icon': 'ri-compass-3-line',
                'icon_bg': '#3b82f6',
                'completed': 32,
                'total': 50,
                'percent': 64,
                'bar_color': '#22c55e',
                'has_dot': True
            },
            {
                'name': 'College Portal',
                'subtitle': 'Academic Management System',
                'icon': 'ri-bank-line',
                'icon_bg': '#475569',
                'completed': 18,
                'total': 30,
                'percent': 60,
                'bar_color': '#f59e0b',
                'has_dot': False
            },
            {
                'name': 'Mobile App',
                'subtitle': 'Android Application',
                'icon': 'ri-smartphone-line',
                'icon_bg': '#ec4899',
                'completed': 12,
                'total': 20,
                'percent': 60,
                'bar_color': '#94a3b8',
                'has_dot': False
            },
            {
                'name': 'Internal Tools',
                'subtitle': 'Company Internal Tools',
                'icon': 'ri-tools-line',
                'icon_bg': '#d97706',
                'completed': 8,
                'total': 15,
                'percent': 53,
                'bar_color': '#f59e0b',
                'has_dot': False
            },
            {
                'name': 'Website Redesign',
                'subtitle': 'Marketing Website',
                'icon': 'ri-window-line',
                'icon_bg': '#0284c7',
                'completed': 6,
                'total': 10,
                'percent': 60,
                'bar_color': '#94a3b8',
                'has_dot': False
            }
        ]
    else:
        # ============================================================
        # EMPLOYEE PERSONALIZED DASHBOARD
        # Shows strictly this employee's tasks, deadlines, and progress
        # ============================================================
        employee_tasks = Task.objects.filter(assignees=user).select_related('project')
        total_tasks = employee_tasks.count()
        completed_tasks = employee_tasks.filter(status='completed').count()
        in_progress_tasks = employee_tasks.filter(status='in_progress').count()
        assigned_tasks = employee_tasks.filter(status__in=['assigned', 'submitted']).count()
        overdue_tasks = employee_tasks.filter(status__in=['assigned', 'in_progress'], due_date__lt=today).count()

        if total_tasks > 0:
            completed_percent = int(completed_tasks / total_tasks * 100)
            in_progress_percent = int(in_progress_tasks / total_tasks * 100)
            assigned_percent = int(assigned_tasks / total_tasks * 100)
            overdue_percent = int(overdue_tasks / total_tasks * 100)
        else:
            completed_percent = 0
            in_progress_percent = 0
            assigned_percent = 0
            overdue_percent = 0

        # Subtask progress for this employee
        subtasks_qs = Subtask.objects.filter(task__assignees=user)
        total_subtasks = subtasks_qs.count()
        completed_subtasks = subtasks_qs.filter(is_completed=True).count()
        subtask_percent = int(completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0

        # Overtime metrics for this employee
        ot_qs = OvertimeRequest.objects.filter(employee=user)
        total_ot_hours = sum(r.requested_hours for r in ot_qs)
        approved_ot_hours = sum(r.approved_hours for r in ot_qs.filter(status='approved'))
        ot_percent = int(approved_ot_hours / total_ot_hours * 100) if total_ot_hours > 0 else 0

        # Personal Upcoming Deadlines
        deadlines = []
        for t in employee_tasks.exclude(status='completed').order_by('due_date')[:5]:
            if t.due_date:
                if t.due_date == today:
                    time_label = 'Today'
                    time_class = 'text-danger'
                elif t.due_date == today + timedelta(days=1):
                    time_label = 'Tomorrow'
                    time_class = 'text-orange'
                elif t.due_date < today:
                    diff = (today - t.due_date).days
                    time_label = f'{diff}d Overdue'
                    time_class = 'text-danger'
                else:
                    time_label = t.due_date.strftime('%d %b %Y')
                    time_class = 'text-muted'
            else:
                time_label = 'No Due Date'
                time_class = 'text-muted'

            priority_map = {
                'urgent': ('Urgent', 'badge-urgent', '#ef4444'),
                'high': ('High', 'badge-high', '#ef4444'),
                'medium': ('Medium', 'badge-medium', '#f59e0b'),
                'low': ('Low', 'badge-low', '#10b981'),
            }
            p_label, p_class, p_color = priority_map.get(t.priority, ('Medium', 'badge-medium', '#3b82f6'))
            deadlines.append({
                'title': t.title,
                'project': f'Project: {t.project.name if t.project else "General"}',
                'time_label': time_label,
                'time_class': time_class,
                'priority': p_label,
                'priority_class': p_class,
                'bar_color': p_color
            })

        if not deadlines:
            deadlines = [{
                'title': 'No pending deadlines',
                'project': 'All assigned tasks completed',
                'time_label': 'All done',
                'time_class': 'text-success',
                'priority': 'Completed',
                'priority_class': 'badge-completed',
                'bar_color': '#22c55e'
            }]

        # Personal Activities only
        activities = []
        user_logs = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:6]
        for log in user_logs:
            icon = 'ri-time-line'
            icon_bg = '#3b82f6'
            if log.action in ('completed', 'approved'):
                icon = 'ri-check-line'
                icon_bg = '#22c55e'
            elif log.action == 'submitted':
                icon = 'ri-send-plane-line'
                icon_bg = '#8b5cf6'
            elif log.action in ('created', 'uploaded'):
                icon = 'ri-add-line'
                icon_bg = '#10b981'
            elif log.action == 'logged_in':
                icon = 'ri-login-box-line'
                icon_bg = '#0284c7'

            now = timezone.now()
            diff = now - log.timestamp
            if diff.days == 0:
                if diff.seconds < 3600:
                    time_str = f'{max(1, diff.seconds // 60)} mins ago'
                else:
                    time_str = f'{diff.seconds // 3600} hours ago'
            else:
                time_str = f'{diff.days} days ago'

            activities.append({
                'icon': icon,
                'icon_bg': icon_bg,
                'title': f'{log.action.title()}: {log.module}',
                'subtitle': log.object_repr,
                'time': time_str,
            })

        if not activities:
            activities = [{
                'icon': 'ri-checkbox-circle-line',
                'icon_bg': '#22c55e',
                'title': 'Welcome to TaskWave',
                'subtitle': 'Your activity will appear here as you work on tasks',
                'time': 'Just now',
            }]

        # Personal Workload & Progress Breakdown
        team_workload = [
            {
                'initials': 'AT',
                'avatar': None,
                'avatar_bg': '#f59e0b',
                'name': 'In Progress Tasks',
                'role': 'Active assignments',
                'completed': in_progress_tasks,
                'total': total_tasks,
                'percent': in_progress_percent,
                'bar_color': '#f59e0b'
            },
            {
                'initials': 'CT',
                'avatar': None,
                'avatar_bg': '#22c55e',
                'name': 'Completed Tasks',
                'role': 'Delivered work',
                'completed': completed_tasks,
                'total': total_tasks,
                'percent': completed_percent,
                'bar_color': '#22c55e'
            },
            {
                'initials': 'ST',
                'avatar': None,
                'avatar_bg': '#3b82f6',
                'name': 'Subtask Checklist',
                'role': 'Subtask items completed',
                'completed': completed_subtasks,
                'total': total_subtasks,
                'percent': subtask_percent,
                'bar_color': '#3b82f6'
            },
            {
                'initials': 'OT',
                'avatar': None,
                'avatar_bg': '#8b5cf6',
                'name': 'Overtime Hours',
                'role': 'Approved / Requested',
                'completed': int(approved_ot_hours),
                'total': int(total_ot_hours),
                'percent': ot_percent,
                'bar_color': '#8b5cf6'
            }
        ]

        # Tasks by Project: prioritize projects where this employee has active assigned tasks
        user_projects = Project.objects.filter(tasks__assignees=user).distinct()
        if not user_projects.exists():
            user_projects = Project.objects.filter(members=user).distinct()

        tasks_by_project = []
        icons = [
            ('ri-macbook-line', '#3b82f6'),
            ('ri-tools-line', '#d97706'),
            ('ri-smartphone-line', '#ec4899'),
            ('ri-window-line', '#0284c7'),
            ('ri-shield-check-line', '#10b981')
        ]
        for idx, p in enumerate(user_projects[:5]):
            p_tasks = employee_tasks.filter(project=p)
            p_total = p_tasks.count()
            p_completed = p_tasks.filter(status='completed').count()
            p_percent = int(p_completed / p_total * 100) if p_total > 0 else 0
            icon, icon_bg = icons[idx % len(icons)]
            tasks_by_project.append({
                'name': p.name,
                'subtitle': f'My assigned tasks in {p.name}',
                'icon': icon,
                'icon_bg': icon_bg,
                'completed': p_completed,
                'total': p_total,
                'percent': p_percent,
                'bar_color': '#22c55e' if p_percent >= 75 else ('#f59e0b' if p_percent >= 30 else '#94a3b8'),
                'has_dot': p_completed > 0
            })

        if not tasks_by_project:
            tasks_by_project = [{
                'name': 'No Project Assignments',
                'subtitle': 'Contact your Project Manager for assignments',
                'icon': 'ri-folder-info-line',
                'icon_bg': '#94a3b8',
                'completed': 0,
                'total': 0,
                'percent': 0,
                'bar_color': '#cbd5e1',
                'has_dot': False
            }]

    # Overview chart data tailored to user scope
    chart_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if is_admin_or_pm:
        chart_completed = [13, 17, 24, 21, 28, 30, 36]
        chart_in_progress = [7, 11, 14, 12, 17, 18, 22]
        chart_overdue = [3, 4, 4, 7, 6, 8, 9]
        chart_assigned = [0, 1, 1, 2, 2, 3, 3]
        chart_max_y = 40
    else:
        chart_completed = [0, 0, 0, 0, 0, completed_tasks, completed_tasks]
        chart_in_progress = [0, 0, 1, 1, 1, in_progress_tasks, in_progress_tasks]
        chart_overdue = [0, 0, 0, 0, 0, overdue_tasks, overdue_tasks]
        chart_assigned = [1, 1, 1, 1, assigned_tasks, assigned_tasks, assigned_tasks]
        chart_max_y = max(5, total_tasks + 2)

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'assigned_tasks': assigned_tasks,
        'overdue_tasks': overdue_tasks,
        'completed_percent': completed_percent,
        'in_progress_percent': in_progress_percent,
        'assigned_percent': assigned_percent,
        'overdue_percent': overdue_percent,
        'deadlines': deadlines,
        'activities': activities,
        'team_workload': team_workload,
        'tasks_by_project': tasks_by_project,
        'is_admin_or_pm': is_admin_or_pm,
        'chart_labels': chart_labels,
        'chart_completed': chart_completed,
        'chart_in_progress': chart_in_progress,
        'chart_overdue': chart_overdue,
        'chart_assigned': chart_assigned,
        'chart_max_y': chart_max_y,
    }

    if request.GET.get('view') == 'admin' and is_admin_or_pm:
        return render(request, 'core/admin_dashboard.html', context)

    return render(request, 'core/dashboard.html', context)


@login_required
def admin_dashboard_view(request):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        from django.contrib import messages
        messages.error(request, "Access denied. Administrator privileges required.")
        return redirect('core:dashboard')
    return render(request, 'core/admin_dashboard.html')


@login_required
def empty_states_view(request):
    return render(request, 'core/empty_states.html')


@login_required
def global_search_view(request):
    query = request.GET.get('q', '').strip()
    results = {
        'tasks': [],
        'projects': [],
        'users': [],
        'query': query
    }
    if query:
        results['tasks'] = Task.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(task_number__icontains=query)
        )[:10]
        results['projects'] = Project.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(project_key__icontains=query)
        )[:10]
        results['users'] = User.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
        )[:10]

    return render(request, 'core/search_results.html', results)


@login_required
def help_support_view(request):
    return render(request, 'core/help_support.html')


# Error handlers
def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_500(request):
    return render(request, 'errors/500.html', status=500)
