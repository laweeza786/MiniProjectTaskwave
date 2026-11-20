import secrets
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from apps.meetings.models import Meeting, MeetingParticipant
from apps.meetings.forms import MeetingForm
from apps.users.models import User
from apps.audit.middleware import log_activity


@login_required
def meeting_list_view(request):
    user = request.user
    now = timezone.now()
    today = now.date()

    status_filter = request.GET.get('status', '').strip().lower()

    # Base counts
    all_meetings = Meeting.objects.all()
    total_meetings = all_meetings.count()
    scheduled_meetings = all_meetings.filter(status='scheduled').count()
    ongoing_meetings = all_meetings.filter(status='ongoing').count()
    completed_meetings = all_meetings.filter(status='completed').count()

    # Determine main section queryset & title dynamically based on filter
    if status_filter == 'completed':
        main_qs = all_meetings.filter(status='completed').order_by('-scheduled_start')
        section_title = "Completed Meetings"
    elif status_filter == 'scheduled':
        main_qs = all_meetings.filter(status='scheduled').order_by('scheduled_start')
        section_title = "Scheduled Meetings"
    elif status_filter == 'ongoing':
        main_qs = all_meetings.filter(status='ongoing').order_by('scheduled_start')
        section_title = "Ongoing Meetings"
    elif status_filter == 'all':
        main_qs = all_meetings.order_by('-scheduled_start')
        section_title = "All Meetings"
    else:
        # Default view: shows only active upcoming meetings (ongoing + scheduled)
        main_qs = all_meetings.filter(status__in=['ongoing', 'scheduled']).order_by('-status', 'scheduled_start')
        section_title = "Upcoming Meetings"

    # Recent (Completed) meetings for the bottom history widget
    recent_qs = all_meetings.filter(status='completed').order_by('-scheduled_start')[:10]

    # Format meetings for display
    main_list = []
    bg_colors = [
        {'bg': '#e0f2fe', 'color': '#0284c7', 'icon': 'ri-video-line'},
        {'bg': '#fee2e2', 'color': '#ef4444', 'icon': 'ri-video-line'},
        {'bg': '#fef3c7', 'color': '#d97706', 'icon': 'ri-video-line'},
        {'bg': '#dcfce7', 'color': '#16a34a', 'icon': 'ri-video-line'},
        {'bg': '#f3e8ff', 'color': '#9333ea', 'icon': 'ri-team-line'},
    ]

    for idx, m in enumerate(main_qs):
        start_dt = m.scheduled_start
        end_dt = m.scheduled_end or (start_dt + timedelta(hours=1))

        if start_dt.date() == today:
            day_str = "Today"
        elif start_dt.date() == today + timedelta(days=1):
            day_str = "Tomorrow"
        elif start_dt.date() == today - timedelta(days=1):
            day_str = "Yesterday"
        else:
            day_str = start_dt.strftime("%d %b %Y")

        time_str = f"{day_str}, {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
        p_count = m.participants.count() or 1

        is_ongoing = (m.status == 'ongoing')
        is_completed = (m.status == 'completed')
        is_scheduled = (m.status == 'scheduled')

        main_list.append({
            'meeting': m,
            'title': m.title,
            'time_str': time_str,
            'p_count': p_count,
            'status': m.status,
            'is_ongoing': is_ongoing,
            'is_completed': is_completed,
            'is_scheduled': is_scheduled,
            'style': bg_colors[idx % len(bg_colors)]
        })

    # Format recent completed meetings
    recent_list = []
    for idx, m in enumerate(recent_qs):
        start_dt = m.scheduled_start
        end_dt = m.scheduled_end or (start_dt + timedelta(hours=1))
        time_str = f"{start_dt.strftime('%d %b %Y')}, {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
        p_count = m.participants.count() or 1

        recent_list.append({
            'meeting': m,
            'title': m.title,
            'time_str': time_str,
            'attendees': p_count,
            'style': bg_colors[idx % len(bg_colors)]
        })

    # Participants list (real active users)
    all_users = User.objects.filter(is_active=True).select_related('role', 'department')
    participants_data = []
    for u in all_users:
        is_current_user = (u.id == user.id)
        role_label = "You (Admin)" if (is_current_user and user.is_superuser) else ("You" if is_current_user else "Online")
        participants_data.append({
            'user': u,
            'name': u.get_full_name() or u.email.split('@')[0],
            'avatar_url': u.avatar.url if getattr(u, 'avatar', None) else None,
            'role_label': role_label,
            'is_muted': False,
            'is_video': True,
        })

    form = MeetingForm()
    selectable_users = all_users.exclude(id=user.id)

    context = {
        'total_meetings': total_meetings,
        'scheduled_meetings': scheduled_meetings,
        'ongoing_meetings': ongoing_meetings,
        'completed_meetings': completed_meetings,
        'status_filter': status_filter,
        'section_title': section_title,
        'main_list': main_list,
        'recent_list': recent_list,
        'participants_data': participants_data,
        'form': form,
        'users': selectable_users,
    }
    return render(request, 'meetings/meeting_list.html', context)


@login_required
def instant_meeting_view(request):
    """Instantly generates a new video meeting room and redirects the user directly into it."""
    meeting_id = f"TW-{secrets.token_hex(3).upper()}"
    title = f"Instant Meeting - {request.user.get_full_name() or 'Team'}"

    meeting = Meeting.objects.create(
        title=title,
        description="Instant ad-hoc video conference meeting.",
        host=request.user,
        scheduled_start=timezone.now(),
        scheduled_end=timezone.now() + timedelta(hours=1),
        actual_start=timezone.now(),
        status='ongoing',
        meeting_id=meeting_id,
        meeting_link=f"/meetings/room/{meeting_id}/",
        allow_screen_sharing=True,
        allow_recording=True,
        allow_chat=True,
    )

    MeetingParticipant.objects.get_or_create(meeting=meeting, user=request.user)
    log_activity(request.user, 'started', 'Meetings', object_type='Meeting', object_id=meeting.id, object_repr=meeting.title, request=request)
    messages.success(request, f'Instant meeting created! Joined room: {meeting_id}')

    return redirect('meetings:room', meeting_id=meeting_id)


@login_required
def meeting_create_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        scheduled_start = request.POST.get('scheduled_start')
        participant_ids = request.POST.getlist('participants')

        if title and scheduled_start:
            meeting_id = f"TW-{secrets.token_hex(3).upper()}"
            meeting = Meeting.objects.create(
                title=title,
                description=description,
                host=request.user,
                scheduled_start=scheduled_start,
                scheduled_end=timezone.now() + timedelta(hours=1),
                status='scheduled',
                meeting_id=meeting_id,
                meeting_link=f"/meetings/room/{meeting_id}/",
                allow_screen_sharing=True,
                allow_recording=True,
                allow_chat=True,
            )

            # Add host as participant
            MeetingParticipant.objects.get_or_create(meeting=meeting, user=request.user)

            # Add selected participants
            for uid in participant_ids:
                if str(uid).isdigit():
                    u = User.objects.filter(id=int(uid)).first()
                    if u:
                        MeetingParticipant.objects.get_or_create(meeting=meeting, user=u)

            log_activity(request.user, 'scheduled', 'Meetings', object_type='Meeting', object_id=meeting.id, object_repr=meeting.title, request=request)
            messages.success(request, f'Meeting "{meeting.title}" scheduled successfully!')
            return redirect('meetings:list')
        else:
            messages.error(request, 'Please provide a title and date/time for the meeting.')

    return redirect('meetings:list')


@login_required
def update_meeting_settings_view(request):
    """AJAX handler for toggling video meeting settings."""
    if request.method == 'POST':
        setting_name = request.POST.get('setting')
        is_enabled = request.POST.get('value') == 'true'
        return JsonResponse({'status': 'success', 'setting': setting_name, 'enabled': is_enabled})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
def meeting_room_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id)
    MeetingParticipant.objects.get_or_create(meeting=meeting, user=request.user)
    participants = meeting.meetingparticipant_set.select_related('user').all()

    return render(request, 'meetings/meeting_room.html', {
        'meeting': meeting,
        'participants': participants,
    })
