"""
Audit Log Models
"""
from django.db import models


class ActivityLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
    ]
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('assigned', 'Assigned'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('logged_in', 'Logged In'),
        ('logged_out', 'Logged Out'),
        ('changed', 'Changed'),
        ('uploaded', 'Uploaded'),
        ('downloaded', 'Downloaded'),
        ('shared', 'Shared'),
        ('deactivated', 'Deactivated'),
        ('activated', 'Activated'),
    ]

    user = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='activity_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    module = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=500, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f'{self.user} - {self.action} - {self.module} at {self.timestamp}'


class SystemSettings(models.Model):
    # Organization
    org_name = models.CharField(max_length=200, default='TaskWave Solutions')
    org_email = models.EmailField(blank=True)
    org_phone = models.CharField(max_length=20, blank=True)
    org_address = models.TextField(blank=True)
    org_website = models.URLField(blank=True)
    org_logo = models.ImageField(upload_to='org/', null=True, blank=True)

    # SMTP Email
    smtp_host = models.CharField(max_length=200, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_username = models.CharField(max_length=200, blank=True)
    smtp_password = models.CharField(max_length=500, blank=True)
    smtp_sender_email = models.EmailField(blank=True)
    smtp_sender_name = models.CharField(max_length=200, blank=True)

    # Appearance
    primary_color = models.CharField(max_length=20, default='#b45309')
    sidebar_style = models.CharField(max_length=20, default='default')
    font_size = models.CharField(max_length=20, default='medium')
    date_format = models.CharField(max_length=50, default='DD MMM YYYY')
    time_format = models.CharField(max_length=20, default='12')
    theme = models.CharField(max_length=20, default='light')

    # Security
    two_factor_auth = models.BooleanField(default=False)
    password_expiry_days = models.PositiveIntegerField(default=90)
    max_login_attempts = models.PositiveIntegerField(default=5)
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    allow_company_network_only = models.BooleanField(default=False)

    # Features
    allow_overtime_requests = models.BooleanField(default=True)
    require_overtime_approval = models.BooleanField(default=True)
    track_overtime_separately = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f'Settings for {self.org_name}'

    @classmethod
    def get_settings(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
