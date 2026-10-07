from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import secrets
from django.utils import timezone

from apps.meetings.models import Meeting, MeetingParticipant
from apps.meetings.forms import MeetingForm
from apps.users.models import User
from apps.audit.middleware import log_activity


@login_required
def meeting_list_view(request):
    user = request.user
    upcoming = Meeting.objects.filter(scheduled_start__gte=timezone.now()).order_by('scheduled_start')
    past = Meeting.objects.filter(scheduled_start__lt=timezone.now()).order_by('-scheduled_start')[:10]

    form = MeetingForm()
    users = User.objects.filter(is_active=True).exclude(id=user.id)

    return render(request, 'meetings/meeting_list.html', {
        'upcoming': upcoming,
        'past': past,
        'form': form,
        'users': users,
    })


@login_required
def meeting_create_view(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.host = request.user
            meeting.meeting_id = secrets.token_hex(4).upper()
            meeting.meeting_link = f'/meetings/room/{meeting.meeting_id}/'
            meeting.save()

            # Add host as participant
            MeetingParticipant.objects.create(meeting=meeting, user=request.user)

            # Add selected participants
            participant_ids = request.POST.getlist('participants')
            for uid in participant_ids:
                u = User.objects.filter(id=uid).first()
                if u:
                    MeetingParticipant.objects.create(meeting=meeting, user=u)

            log_activity(request.user, 'created', 'Meetings', object_type='Meeting', object_id=meeting.id, object_repr=meeting.title, request=request)
            messages.success(request, f'Meeting "{meeting.title}" scheduled!')
    return redirect('meetings:list')


@login_required
def meeting_room_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id)
    participants = meeting.meetingparticipant_set.select_related('user').all()

    return render(request, 'meetings/meeting_room.html', {
        'meeting': meeting,
        'participants': participants,
    })
