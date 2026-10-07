"""
Task Models - Core of TaskWave
"""
from django.db import models
from django.utils import timezone


class TaskCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, default='#6b7280')
    icon = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'task_categories'
        verbose_name_plural = 'Task Categories'

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted for Review'),
        ('under_review', 'Under Review'),
        ('changes_requested', 'Changes Requested'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    VISIBILITY_CHOICES = [
        ('project_members', 'Project Members'),
        ('department', 'Department'),
        ('organization', 'Organization'),
    ]

    # Identity
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    task_number = models.CharField(max_length=20, unique=True, blank=True)

    # Relations
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE,
        related_name='tasks', null=True, blank=True
    )
    department = models.ForeignKey(
        'departments.Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tasks'
    )
    category = models.ForeignKey(
        TaskCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tasks'
    )
    tags = models.CharField(max_length=500, blank=True)
    assignees = models.ManyToManyField(
        'users.User', through='TaskAssignee', through_fields=('task', 'user'), related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='created_tasks'
    )

    # Dates
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Status & Priority
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='assigned')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='project_members')

    # Progress
    progress = models.PositiveIntegerField(default=0)  # 0-100
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)

    # Dependencies
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependents')
    related_tasks = models.ManyToManyField('self', blank=True, symmetrical=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.task_number}: {self.title}'

    def save(self, *args, **kwargs):
        if not self.task_number:
            last = Task.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            prefix = self.project.project_key if self.project else 'TW'
            self.task_number = f'#{prefix}-{num:04d}'
        super().save(*args, **kwargs)

    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False

    def days_remaining(self):
        if self.due_date:
            delta = self.due_date - timezone.now().date()
            return delta.days
        return None

    def get_subtask_progress(self):
        subtasks = self.subtasks.all()
        total = subtasks.count()
        if total == 0:
            return 0
        completed = subtasks.filter(is_completed=True).count()
        return round((completed / total) * 100)

    def get_primary_assignee(self):
        assignee = self.taskassignee_set.filter(is_primary=True).first()
        if assignee:
            return assignee.user
        return self.taskassignee_set.first().user if self.taskassignee_set.exists() else None


class TaskAssignee(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='task_assignments_made'
    )

    class Meta:
        db_table = 'task_assignees'
        unique_together = ['task', 'user']


class Subtask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=500)
    is_completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'subtasks'
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        db_table = 'task_comments'
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user} on {self.task}'


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    original_filename = models.CharField(max_length=500)
    file_size = models.PositiveBigIntegerField(default=0)
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_attachments'

    def __str__(self):
        return self.original_filename

    def file_size_display(self):
        size = self.file_size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        else:
            return f'{size / (1024 * 1024):.1f} MB'


class TaskSubmission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('changes_requested', 'Changes Requested'),
        ('rejected', 'Rejected'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='task_submissions'
    )
    version = models.PositiveIntegerField(default=1)
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_submissions'
        ordering = ['-submitted_at']

    def __str__(self):
        return f'Submission v{self.version} for {self.task}'


class TaskSubmissionFile(models.Model):
    submission = models.ForeignKey(TaskSubmission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='submissions/')
    original_filename = models.CharField(max_length=500)
    file_size = models.PositiveBigIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_submission_files'


class TaskReview(models.Model):
    submission = models.OneToOneField(TaskSubmission, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey('users.User', on_delete=models.CASCADE)
    decision = models.CharField(max_length=30, choices=[
        ('approved', 'Approved'),
        ('changes_requested', 'Changes Requested'),
        ('rejected', 'Rejected'),
    ])
    comments = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_reviews'


class TaskStatusHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_status_history'
        ordering = ['-changed_at']
