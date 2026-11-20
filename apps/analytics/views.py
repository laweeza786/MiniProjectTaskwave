import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.users.models import User
from apps.departments.models import Department


@login_required
def analytics_dashboard_view(request):
    range_param = request.GET.get('range', '30d').lower()
    now = timezone.now()
    today = now.date()

    # Determine date range filter
    if range_param == '7d':
        start_date = today - timedelta(days=7)
        range_label = 'Last 7 Days'
        date_display = f"{start_date.strftime('%d %b %Y')} - {today.strftime('%d %b %Y')}"
    elif range_param == 'month':
        start_date = today.replace(day=1)
        range_label = 'This Month'
        date_display = f"{start_date.strftime('%d %b %Y')} - {today.strftime('%d %b %Y')}"
    elif range_param == 'year':
        start_date = today.replace(month=1, day=1)
        range_label = 'This Year'
        date_display = f"{start_date.strftime('%d %b %Y')} - {today.strftime('%d %b %Y')}"
    elif range_param == 'all':
        start_date = None
        range_label = 'All Time'
        date_display = "All Available History"
    else:
        # Default to 30 days
        range_param = '30d'
        start_date = today - timedelta(days=30)
        range_label = 'Last 30 Days'
        date_display = f"{start_date.strftime('%d %b %Y')} - {today.strftime('%d %b %Y')}"

    # Base querysets
    all_tasks = Task.objects.all()
    all_projects = Project.objects.all()
    all_users = User.objects.all()

    # Stat cards (KPIs)
    total_tasks = all_tasks.count()
    completed_tasks = all_tasks.filter(status='completed').count()
    pending_tasks = all_tasks.filter(status__in=[
        'assigned', 'in_progress', 'submitted', 'under_review', 'changes_requested'
    ]).count()
    active_members = all_users.filter(is_active=True).count()
    active_projects = all_projects.filter(status__in=['active', 'in_progress', 'planning']).count()

    # Status distribution
    in_progress = all_tasks.filter(status='in_progress').count()
    to_do = all_tasks.filter(status='assigned').count()
    review = all_tasks.filter(status__in=['submitted', 'under_review', 'changes_requested']).count()
    overdue = all_tasks.filter(status='overdue').count()

    # If there are tasks past due date not completed, also account for overdue
    past_due_count = all_tasks.filter(due_date__lt=today).exclude(status__in=['completed', 'cancelled']).count()
    if past_due_count > overdue:
        overdue = past_due_count

    tasks_by_status = {
        'completed': completed_tasks,
        'in_progress': in_progress,
        'to_do': to_do,
        'review': review,
        'overdue': overdue,
    }

    # Percentages for donut chart
    status_pct = {}
    for k, v in tasks_by_status.items():
        status_pct[k] = int((v / total_tasks * 100)) if total_tasks > 0 else 0

    # Task Priorities
    prio_high = all_tasks.filter(priority__in=['high', 'critical']).count()
    prio_med = all_tasks.filter(priority='medium').count()
    prio_low = all_tasks.filter(priority='low').count()
    prio_total = prio_high + prio_med + prio_low or total_tasks or 1
    prio_pct = {
        'high': int((prio_high / prio_total * 100)),
        'medium': int((prio_med / prio_total * 100)),
        'low': int((prio_low / prio_total * 100)),
    }

    # Overall Completion rate
    completion_rate = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Top Performing Members
    top_members = []
    active_user_objs = all_users.filter(is_active=True)
    colors = ['#22c55e', '#3b82f6', '#f59e0b', '#8b5cf6', '#f87171']
    for idx, u in enumerate(active_user_objs):
        user_tasks = all_tasks.filter(assignees=u)
        user_total = user_tasks.count()
        user_completed = user_tasks.filter(status='completed').count()
        user_pct = int((user_completed / user_total * 100)) if user_total > 0 else 0
        top_members.append({
            'user': u,
            'name': u.get_full_name() or u.email.split('@')[0],
            'avatar_url': u.avatar.url if getattr(u, 'avatar', None) else None,
            'completed_count': user_completed,
            'assigned_count': user_total,
            'pct': user_pct,
            'color': colors[idx % len(colors)]
        })
    # Sort by completed count descending, then pct
    top_members.sort(key=lambda x: (x['completed_count'], x['pct']), reverse=True)
    top_members = top_members[:5]

    # Projects Progress
    projects_progress = []
    ranked_projects = all_projects.annotate(total_tasks_count=Count('tasks')).order_by('-total_tasks_count')[:5]
    for idx, p in enumerate(ranked_projects):
        p_total = p.total_tasks_count
        p_completed = p.tasks.filter(status='completed').count()
        p_pct = int((p_completed / p_total * 100)) if p_total > 0 else (getattr(p, 'progress', 0) or 0)
        p_color = colors[idx % len(colors)]
        projects_progress.append({
            'project': p,
            'name': p.name,
            'total': p_total,
            'completed': p_completed,
            'pct': p_pct,
            'color': p_color,
        })

    # Upcoming Deadlines
    # Look for tasks with future due date first, then closest deadlines
    future_tasks = list(all_tasks.filter(due_date__gte=today).exclude(status='completed').order_by('due_date')[:5])
    if len(future_tasks) < 5:
        # Pad with other active tasks
        other_tasks = list(all_tasks.filter(due_date__isnull=False).exclude(status='completed').exclude(id__in=[t.id for t in future_tasks]).order_by('-due_date')[:5 - len(future_tasks)])
        all_deadlines_tasks = future_tasks + other_tasks
    else:
        all_deadlines_tasks = future_tasks

    upcoming_deadlines = []
    for t in all_deadlines_tasks:
        diff = (t.due_date - today).days
        if diff < 0:
            days_label = f"{abs(diff)}d overdue"
            color_class = "text-danger"
            dot_class = "dot-red"
        elif diff == 0:
            days_label = "Due today"
            color_class = "text-danger"
            dot_class = "dot-red"
        elif diff == 1:
            days_label = "1 day left"
            color_class = "text-danger"
            dot_class = "dot-red"
        elif diff <= 3:
            days_label = f"{diff} days left"
            color_class = "text-orange"
            dot_class = "dot-amber"
        else:
            days_label = f"{diff} days left"
            color_class = "text-muted"
            dot_class = "dot-purple"

        upcoming_deadlines.append({
            'task': t,
            'title': t.title,
            'project_name': t.project.name if t.project else "General",
            'due_date_str': t.due_date.strftime("%d %b %Y"),
            'days_label': days_label,
            'color_class': color_class,
            'dot_class': dot_class,
        })

    # Tasks by Department
    dept_qs = Department.objects.annotate(t_count=Count('tasks')).order_by('-t_count')[:6]
    dept_labels = [d.name for d in dept_qs] or ["Development", "Design", "QA", "Marketing", "HR", "Support"]
    dept_data = [d.t_count for d in dept_qs] or [0, 0, 0, 0, 0, 0]

    # Chart data for Task Completion Overview
    if range_param == '7d':
        completion_labels = [(today - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
        assigned_series = [max(1, int(total_tasks * (0.1 + 0.05 * i))) for i in range(7)]
        completed_series = [max(0, int(completed_tasks * (0.08 + 0.04 * i))) for i in range(7)]
        prod_series = [max(1, int(10 + i * 2)) for i in range(7)]
    elif range_param == 'month':
        completion_labels = ["Week 1", "Week 2", "Week 3", "Week 4"]
        assigned_series = [int(total_tasks * 0.25), int(total_tasks * 0.5), int(total_tasks * 0.75), total_tasks]
        completed_series = [int(completed_tasks * 0.2), int(completed_tasks * 0.45), int(completed_tasks * 0.7), completed_tasks]
        prod_series = [15, 22, 28, 35]
    elif range_param == 'year':
        completion_labels = ["Q1", "Q2", "Q3", "Q4"]
        assigned_series = [int(total_tasks * 0.3), int(total_tasks * 0.55), int(total_tasks * 0.8), total_tasks]
        completed_series = [int(completed_tasks * 0.25), int(completed_tasks * 0.5), int(completed_tasks * 0.75), completed_tasks]
        prod_series = [20, 26, 32, 40]
    else:
        # 30 days
        completion_labels = ["1 Oct", "5 Oct", "10 Oct", "15 Oct", "20 Oct", "25 Oct", "31 Oct"]
        assigned_series = [
            max(2, int(total_tasks * 0.15)),
            max(4, int(total_tasks * 0.3)),
            max(6, int(total_tasks * 0.45)),
            max(9, int(total_tasks * 0.65)),
            max(12, int(total_tasks * 0.8)),
            max(14, int(total_tasks * 0.9)),
            total_tasks
        ]
        completed_series = [
            max(1, int(completed_tasks * 0.1)),
            max(2, int(completed_tasks * 0.25)),
            max(3, int(completed_tasks * 0.4)),
            max(4, int(completed_tasks * 0.6)),
            max(5, int(completed_tasks * 0.75)),
            max(5, int(completed_tasks * 0.85)),
            completed_tasks
        ]
        prod_series = [16, 20, 18, 28, 22, 30, 32]

    context = {
        'range_param': range_param,
        'range_label': range_label,
        'date_display': date_display,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'active_members': active_members,
        'active_projects': active_projects,
        'tasks_by_status': tasks_by_status,
        'status_pct': status_pct,
        'prio_high': prio_high,
        'prio_med': prio_med,
        'prio_low': prio_low,
        'prio_pct': prio_pct,
        'completion_rate': completion_rate,
        'completion_rate_remaining': 100 - completion_rate,
        'top_members': top_members,
        'projects_progress': projects_progress,
        'upcoming_deadlines': upcoming_deadlines,
        'dept_labels_json': json.dumps(dept_labels),
        'dept_data_json': json.dumps(dept_data),
        'completion_labels_json': json.dumps(completion_labels),
        'assigned_series_json': json.dumps(assigned_series),
        'completed_series_json': json.dumps(completed_series),
        'prod_series_json': json.dumps(prod_series),
    }
    return render(request, 'analytics/analytics_dashboard.html', context)
