"""
Notification Models
"""
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('task_overdue', 'Task Overdue'),
        ('task_submitted', 'Task Submitted'),
        ('task_approved', 'Task Approved'),
        ('changes_requested', 'Changes Requested'),
        ('new_message', 'New Message'),
        ('mention', 'Mention'),
        ('project_update', 'Project Update'),
        ('overtime_request', 'Overtime Request'),
        ('overtime_decision', 'Overtime Decision'),
        ('meeting_invite', 'Meeting Invitation'),
        ('file_shared', 'File Shared'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('member_joined', 'Member Joined'),
        ('system', 'System'),
    ]

    recipient = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=300)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    url = models.CharField(max_length=500, blank=True)
    related_object_type = models.CharField(max_length=100, blank=True)
    related_object_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sent_notifications'
    )

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.notification_type} for {self.recipient}'

    def mark_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        'users.User', on_delete=models.CASCADE, related_name='notification_preferences'
    )
    email_notifications = models.BooleanField(default=True)
    browser_notifications = models.BooleanField(default=True)
    task_updates = models.BooleanField(default=True)
    project_updates = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    overtime_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'

    def __str__(self):
        return f'Preferences for {self.user}'
