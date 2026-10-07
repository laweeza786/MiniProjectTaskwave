"""
Calendar Event Models
"""
from django.db import models


class CalendarEvent(models.Model):
    TYPE_CHOICES = [
        ('task_deadline', 'Task Deadline'),
        ('meeting', 'Meeting'),
        ('project_milestone', 'Project Milestone'),
        ('review', 'Review'),
        ('training', 'Training'),
        ('other', 'Other'),
    ]
    COLOR_MAP = {
        'task_deadline': '#ef4444',
        'meeting': '#3b82f6',
        'project_milestone': '#8b5cf6',
        'review': '#f59e0b',
        'training': '#10b981',
        'other': '#6b7280',
    }

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='other')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=300, blank=True)
    color = models.CharField(max_length=20, blank=True)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.SET_NULL, null=True, blank=True
    )
    task = models.ForeignKey(
        'tasks.Task', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_by = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='created_events'
    )
    attendees = models.ManyToManyField('users.User', blank=True, related_name='calendar_events')
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendar_events'
        ordering = ['start_datetime']

    def __str__(self):
        return self.title

    def get_color(self):
        return self.color or self.COLOR_MAP.get(self.event_type, '#6b7280')
