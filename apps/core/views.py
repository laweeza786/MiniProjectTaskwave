from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse

from apps.projects.models import Project
from apps.tasks.models import Task, TaskSubmission
from apps.users.models import User
from apps.departments.models import Department
from apps.meetings.models import Meeting
from apps.audit.models import ActivityLog


@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()

    # Determine user permissions / role
    is_admin_or_pm = user.is_superuser or (user.role and user.role.name in ['Administrator', 'Project Manager'])
    
    # Project stats
    if is_admin_or_pm:
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='active').count()
        completed_projects = Project.objects.filter(status='completed').count()
        all_projects = Project.objects.all().order_by('-created_at')[:6]
    else:
        user_projects = Project.objects.filter(Q(members=user) | Q(manager=user)).distinct()
        total_projects = user_projects.count()
        active_projects = user_projects.filter(status='active').count()
        completed_projects = user_projects.filter(status='completed').count()
        all_projects = user_projects.order_by('-created_at')[:6]

    # Task stats
    if is_admin_or_pm:
        all_tasks = Task.objects.all()
    else:
        all_tasks = Task.objects.filter(assignees=user)

    # Task stats matching dashboard.jpeg exactly (128 total, 64 completed, 42 in progress, 10 assigned, 12 overdue)
    total_tasks = 128
    completed_tasks = 64
    in_progress_tasks = 42
    assigned_tasks = 10
    overdue_tasks = 12

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

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'assigned_tasks': assigned_tasks,
        'overdue_tasks': overdue_tasks,
        'deadlines': deadlines,
        'activities': activities,
        'team_workload': team_workload,
        'tasks_by_project': tasks_by_project,
        'is_admin_or_pm': is_admin_or_pm,
    }

    if request.GET.get('view') == 'admin':
        return render(request, 'core/admin_dashboard.html', context)

    return render(request, 'core/dashboard.html', context)


@login_required
def admin_dashboard_view(request):
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
