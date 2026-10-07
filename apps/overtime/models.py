"""
Overtime Models
"""
from django.db import models


class OvertimeRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='overtime_requests'
    )
    project = models.ForeignKey(
        'projects.Project', on_delete=models.SET_NULL, null=True, blank=True
    )
    task = models.ForeignKey(
        'tasks.Task', on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField()
    department = models.ForeignKey(
        'departments.Department', on_delete=models.SET_NULL, null=True, blank=True
    )
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    requested_hours = models.DecimalField(max_digits=5, decimal_places=1)
    approved_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_overtime'
    )
    review_comment = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'overtime_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f'OT Request - {self.employee} ({self.start_date})'

    def total_hours(self):
        return self.approved_hours or self.requested_hours

    def total_amount(self):
        if self.hourly_rate and self.approved_hours:
            return float(self.hourly_rate) * float(self.approved_hours)
        return None
