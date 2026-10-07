"""
Meeting Models
"""
from django.db import models


class Meeting(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    host = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='hosted_meetings'
    )
    participants = models.ManyToManyField(
        'users.User', through='MeetingParticipant', related_name='meetings'
    )
    project = models.ForeignKey(
        'projects.Project', on_delete=models.SET_NULL, null=True, blank=True
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    meeting_link = models.URLField(blank=True)
    meeting_id = models.CharField(max_length=100, blank=True)
    allow_screen_sharing = models.BooleanField(default=True)
    allow_recording = models.BooleanField(default=True)
    waiting_room = models.BooleanField(default=False)
    require_host_approval = models.BooleanField(default=False)
    auto_mute_on_join = models.BooleanField(default=False)
    allow_chat = models.BooleanField(default=True)
    allow_file_sharing = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meetings'
        ordering = ['scheduled_start']

    def __str__(self):
        return self.title

    def participant_count(self):
        return self.participants.count()


class MeetingParticipant(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    is_muted = models.BooleanField(default=False)
    is_video_on = models.BooleanField(default=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meeting_participants'
        unique_together = ['meeting', 'user']
