from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import csv
from apps.tasks.models import Task
from apps.projects.models import Project


@login_required
def reports_overview_view(request):
    projects = Project.objects.all()
    tasks = Task.objects.all()
    return render(request, 'reports/reports_overview.html', {'projects': projects, 'tasks': tasks})


@login_required
def export_tasks_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="taskwave_tasks.csv"'

    writer = csv.writer(response)
    writer.writerow(['Task Number', 'Title', 'Project', 'Status', 'Priority', 'Progress', 'Due Date'])

    for t in Task.objects.select_related('project').all():
        writer.writerow([
            t.task_number,
            t.title,
            t.project.name if t.project else 'N/A',
            t.status,
            t.priority,
            f'{t.progress}%',
            t.due_date or 'No date'
        ])

    return response


@login_required
def export_projects_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="taskwave_projects.csv"'

    writer = csv.writer(response)
    writer.writerow(['Key', 'Name', 'Status', 'Priority', 'Manager', 'Progress'])

    for p in Project.objects.select_related('manager').all():
        writer.writerow([
            p.project_key,
            p.name,
            p.status,
            p.priority,
            p.manager.get_full_name() if p.manager else 'Unassigned',
            f'{p.get_progress()}%'
        ])

    return response
