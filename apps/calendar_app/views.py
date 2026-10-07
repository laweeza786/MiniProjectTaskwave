from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from apps.calendar_app.models import CalendarEvent
from apps.projects.models import Project
from apps.tasks.models import Task


@login_required
def calendar_view(request):
    projects = Project.objects.all()
    tasks = Task.objects.filter(assignees=request.user)
    return render(request, 'calendar_app/calendar.html', {'projects': projects, 'tasks': tasks})


@login_required
def calendar_events_json(request):
    events = CalendarEvent.objects.all()
    events_data = []
    for ev in events:
        events_data.append({
            'id': ev.id,
            'title': ev.title,
            'start': ev.start_datetime.isoformat(),
            'end': ev.end_datetime.isoformat() if ev.end_datetime else None,
            'color': ev.get_color(),
            'allDay': ev.all_day,
            'description': ev.description,
            'location': ev.location,
        })
    
    # Also add tasks with due dates as calendar events
    tasks = Task.objects.filter(due_date__isnull=False)
    for t in tasks:
        events_data.append({
            'id': f'task-{t.id}',
            'title': f'Task: {t.title}',
            'start': t.due_date.isoformat(),
            'color': '#ef4444' if t.is_overdue() else '#3b82f6',
            'allDay': True,
            'url': f'/tasks/{t.id}/',
        })

    return JsonResponse(events_data, safe=False)


@login_required
def add_calendar_event(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        event_type = request.POST.get('event_type', 'other')
        start = request.POST.get('start_datetime')
        end = request.POST.get('end_datetime') or None
        location = request.POST.get('location', '')
        desc = request.POST.get('description', '')

        if title and start:
            CalendarEvent.objects.create(
                title=title,
                event_type=event_type,
                start_datetime=start,
                end_datetime=end,
                location=location,
                description=desc,
                created_by=request.user
            )
            return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)
