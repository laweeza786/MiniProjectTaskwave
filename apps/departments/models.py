"""
Department Models
"""
from django.db import models


class Department(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='headed_departments'
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    icon = models.CharField(max_length=100, blank=True, default='bi-building')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        ordering = ['name']

    def __str__(self):
        return self.name

    def member_count(self):
        return self.members.filter(is_active=True).count()

    def project_count(self):
        return self.projects.count()
