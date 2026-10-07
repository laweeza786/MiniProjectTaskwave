from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.users.models import User
from apps.departments.models import Department


@login_required
def analytics_dashboard_view(request):
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='completed').count()
    in_progress = Task.objects.filter(status='in_progress').count()
    overdue = Task.objects.filter(status='overdue').count()

    tasks_by_priority = {
        'critical': Task.objects.filter(priority='critical').count(),
        'high': Task.objects.filter(priority='high').count(),
        'medium': Task.objects.filter(priority='medium').count(),
        'low': Task.objects.filter(priority='low').count(),
    }

    tasks_by_status = {
        'completed': completed_tasks,
        'in_progress': in_progress,
        'assigned': Task.objects.filter(status='assigned').count(),
        'review': Task.objects.filter(status__in=['submitted', 'under_review']).count(),
        'changes': Task.objects.filter(status='changes_requested').count(),
    }

    # Department task distribution
    departments = Department.objects.annotate(dept_tasks=Count('tasks')).all()

    # Projects progress
    projects = Project.objects.annotate(project_tasks=Count('tasks')).all()[:8]

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress': in_progress,
        'overdue': overdue,
        'tasks_by_priority': tasks_by_priority,
        'tasks_by_status': tasks_by_status,
        'departments': departments,
        'projects': projects,
    }
    return render(request, 'analytics/analytics_dashboard.html', context)
