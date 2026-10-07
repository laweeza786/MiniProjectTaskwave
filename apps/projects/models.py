"""
Project Models
"""
from django.db import models


class Project(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    CATEGORY_CHOICES = [
        ('web_application', 'Web Application'),
        ('mobile_app', 'Mobile App'),
        ('api', 'API'),
        ('design', 'Design'),
        ('research', 'Research'),
        ('other', 'Other'),
    ]
    VISIBILITY_CHOICES = [
        ('project_members', 'Project Members Only'),
        ('department', 'Department'),
        ('organization', 'Organization'),
    ]

    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        'departments.Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='projects'
    )
    manager = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managed_projects'
    )
    members = models.ManyToManyField(
        'users.User', through='ProjectMember', related_name='projects'
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    project_key = models.CharField(max_length=20, unique=True, blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='project_members')
    goals = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)
    client = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=20, blank=True, default='#3b82f6')
    is_starred = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='created_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.project_key:
            words = self.name.split()
            key = ''.join([w[0].upper() for w in words[:3]])
            self.project_key = f'TW-{key}'
        super().save(*args, **kwargs)

    def get_progress(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter(status='completed').count()
        return round((completed / total) * 100)

    def get_task_counts(self):
        tasks = self.tasks.all()
        return {
            'total': tasks.count(),
            'completed': tasks.filter(status='completed').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'not_started': tasks.filter(status='assigned').count(),
            'overdue': tasks.filter(status='overdue').count(),
        }


class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_members'
        unique_together = ['project', 'user']

    def __str__(self):
        return f'{self.user} - {self.project}'


class ProjectMilestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=300)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_milestones'
        ordering = ['due_date']

    def __str__(self):
        return f'{self.project.name} - {self.title}'
