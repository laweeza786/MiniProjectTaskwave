from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime

from apps.calendar_app.models import CalendarEvent
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.users.models import User


def ensure_sample_calendar_events(user):
    """Seed sample events if database has few events, matching calender.jpeg design."""
    if CalendarEvent.objects.count() >= 8:
        return

    sample_items = [
        ('Project Planning', 'Initial sprint backlog and timeline planning.', 'meeting', '2026-09-30 10:00:00', '2026-09-30 11:00:00', 'Online Zoom', '#3b82f6'),
        ('UI Design Review', 'Figma design tokens and component audit.', 'review', '2026-10-02 11:00:00', '2026-10-02 12:00:00', 'Meeting Room 2', '#ef4444'),
        ('Database Setup', 'PostgreSQL / MySQL replication configuration.', 'project_milestone', '2026-10-06 09:00:00', '2026-10-06 11:00:00', 'Server Room', '#10b981'),
        ('Team Meeting', 'Weekly engineering sync and blocker clearing.', 'meeting', '2026-10-07 14:00:00', '2026-10-07 15:00:00', 'Conference Room A', '#f59e0b'),
        ('API Development', 'Build REST endpoints for mobile client.', 'task_deadline', '2026-10-09 10:00:00', '2026-10-09 13:00:00', 'Dev Floor', '#3b82f6'),
        ('Client Review', 'Sprint milestone demonstration to stakeholders.', 'review', '2026-10-14 11:00:00', '2026-10-14 12:00:00', 'Boardroom', '#ef4444'),
        ('Testing & QA', 'End-to-end Cypress regression testing run.', 'training', '2026-10-15 09:00:00', '2026-10-15 12:00:00', 'Development Lab', '#10b981'),
        ('Design Discussion', 'Design system typography and responsive grids.', 'meeting', '2026-10-17 14:00:00', '2026-10-17 15:00:00', 'Meeting Room 1', '#8b5cf6'),
        ('Documentation', 'Update API docs and developer onboarding manual.', 'other', '2026-10-20 10:00:00', '2026-10-20 13:00:00', 'Online Meet', '#3b82f6'),
        ('Sprint Planning', 'Sprint 15 backlog grooming and estimation.', 'meeting', '2026-10-22 11:00:00', '2026-10-22 12:00:00', 'War Room', '#f59e0b'),
        ('Security Testing', 'Vulnerability scanning and pen testing assessment.', 'review', '2026-10-23 09:00:00', '2026-10-23 11:00:00', 'IT Lab', '#ef4444'),
        ('Final Review', 'Final QA sign-off and release validation.', 'review', '2026-10-27 14:00:00', '2026-10-27 16:00:00', 'Meeting Room B', '#10b981'),
        ('Deployment', 'Production server deployment and smoke testing.', 'project_milestone', '2026-10-28 10:00:00', '2026-10-28 12:00:00', 'DevOps Ops Center', '#3b82f6'),
        ('Project Presentation', 'Executive leadership project wrap-up presentation.', 'meeting', '2026-10-30 11:00:00', '2026-10-30 13:00:00', 'Auditorium', '#f59e0b'),
    ]

    project = Project.objects.first()
    all_users = list(User.objects.filter(is_active=True)[:4])

    for title, desc, etype, s_str, e_str, loc, col in sample_items:
        if not CalendarEvent.objects.filter(title=title).exists():
            s_dt = timezone.make_aware(datetime.strptime(s_str, '%Y-%m-%d %H:%M:%S'))
            e_dt = timezone.make_aware(datetime.strptime(e_str, '%Y-%m-%d %H:%M:%S'))
            ev = CalendarEvent.objects.create(
                title=title,
                description=desc,
                event_type=etype,
                start_datetime=s_dt,
                end_datetime=e_dt,
                location=loc,
                color=col,
                project=project,
                created_by=user
            )
            if all_users:
                ev.attendees.set(all_users[:2])


@login_required
def calendar_view(request):
    ensure_sample_calendar_events(request.user)

    projects = Project.objects.all().order_by('name')
    members = User.objects.filter(is_active=True).order_by('first_name')
    event_types = CalendarEvent.TYPE_CHOICES

    # Upcoming events from today or next upcoming
    upcoming_events = CalendarEvent.objects.all().select_related('project', 'created_by').prefetch_related('attendees').order_by('start_datetime')[:6]

    context = {
        'projects': projects,
        'members': members,
        'event_types': event_types,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'calendar_app/calendar.html', context)


@login_required
def calendar_events_json(request):
    project_filter = request.GET.get('project', '')
    member_filter = request.GET.get('member', '')
    type_filter = request.GET.get('event_type', '')

    events = CalendarEvent.objects.all().select_related('project', 'created_by').prefetch_related('attendees')

    if project_filter:
        events = events.filter(project_id=project_filter)
    if member_filter:
        events = events.filter(attendees__id=member_filter)
    if type_filter:
        events = events.filter(event_type=type_filter)

    events_data = []
    for ev in events:
        attendees_data = []
        for a in ev.attendees.all():
            avatar_url = a.profile_picture.url if hasattr(a, 'profile_picture') and a.profile_picture else '/static/img/avatars/rahul_kumar.jpg'
            attendees_data.append({
                'id': a.id,
                'name': a.get_full_name(),
                'avatar': avatar_url,
            })

        events_data.append({
            'id': ev.id,
            'title': ev.title,
            'start': ev.start_datetime.strftime('%Y-%m-%dT%H:%M:%S') if ev.start_datetime else '',
            'end': ev.end_datetime.strftime('%Y-%m-%dT%H:%M:%S') if ev.end_datetime else None,
            'start_date': ev.start_datetime.strftime('%Y-%m-%d') if ev.start_datetime else '',
            'start_time': ev.start_datetime.strftime('%I:%M %p') if ev.start_datetime else '',
            'end_time': ev.end_datetime.strftime('%I:%M %p') if ev.end_datetime else '',
            'color': ev.get_color(),
            'event_type': ev.event_type,
            'event_type_display': ev.get_event_type_display(),
            'description': ev.description,
            'location': ev.location,
            'project': ev.project.name if ev.project else 'General',
            'project_id': ev.project.id if ev.project else None,
            'attendees': attendees_data,
        })

    return JsonResponse({'success': True, 'events': events_data})


@login_required
def add_calendar_event(request):
    if request.method == 'POST':
        # Accept JSON or form-data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except Exception:
                data = {}
        else:
            data = request.POST

        title = data.get('title', '').strip()
        event_type = data.get('event_type', 'other')
        start = data.get('start_datetime', '').strip()
        end = data.get('end_datetime', '').strip() or None
        location = data.get('location', '').strip()
        desc = data.get('description', '').strip()
        project_id = data.get('project')
        attendee_ids = data.getlist('attendees') if hasattr(data, 'getlist') else data.get('attendees', [])

        if not title:
            return JsonResponse({'success': False, 'error': 'Event title is required'}, status=400)
        if not start:
            return JsonResponse({'success': False, 'error': 'Start date and time is required'}, status=400)

        # Parse start and end datetimes
        start_dt = None
        for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                start_dt = datetime.strptime(start, fmt)
                break
            except ValueError:
                pass

        if not start_dt:
            return JsonResponse({'success': False, 'error': 'Invalid start date format'}, status=400)
        start_dt = timezone.make_aware(start_dt) if timezone.is_naive(start_dt) else start_dt

        end_dt = None
        if end:
            for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
                try:
                    end_dt = datetime.strptime(end, fmt)
                    break
                except ValueError:
                    pass
            if end_dt:
                end_dt = timezone.make_aware(end_dt) if timezone.is_naive(end_dt) else end_dt

        project = None
        if project_id:
            try:
                project = Project.objects.filter(id=project_id).first()
            except (ValueError, TypeError):
                pass

        color_map = CalendarEvent.COLOR_MAP
        event_color = color_map.get(event_type, '#6b7280')

        event = CalendarEvent.objects.create(
            title=title,
            event_type=event_type,
            start_datetime=start_dt,
            end_datetime=end_dt,
            location=location,
            description=desc,
            project=project,
            color=event_color,
            created_by=request.user
        )

        if attendee_ids:
            attendee_users = User.objects.filter(id__in=attendee_ids)
            event.attendees.set(attendee_users)

        return JsonResponse({
            'success': True,
            'message': 'Event created successfully!',
            'event': {
                'id': event.id,
                'title': event.title,
                'start': event.start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'start_date': event.start_datetime.strftime('%Y-%m-%d'),
                'start_time': event.start_datetime.strftime('%I:%M %p'),
                'end_time': event.end_datetime.strftime('%I:%M %p') if event.end_datetime else '',
                'color': event.get_color(),
                'event_type': event.event_type,
                'event_type_display': event.get_event_type_display(),
                'location': event.location,
                'project': event.project.name if event.project else 'General',
            }
        })
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def delete_calendar_event(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(CalendarEvent, id=event_id)
        event.delete()
        return JsonResponse({'success': True, 'message': 'Event deleted successfully.'})
    return JsonResponse({'error': 'POST required'}, status=405)
