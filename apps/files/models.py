"""
File Management Models
"""
from django.db import models


class ProjectFile(models.Model):
    name = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=500)
    file = models.FileField(upload_to='project_files/')
    file_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE,
        null=True, blank=True, related_name='files'
    )
    task = models.ForeignKey(
        'tasks.Task', on_delete=models.CASCADE,
        null=True, blank=True, related_name='files'
    )
    uploaded_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'project_files'
        ordering = ['-uploaded_at']

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

    def get_file_icon(self):
        ext = self.original_filename.lower().split('.')[-1] if '.' in self.original_filename else ''
        icons = {
            'pdf': 'bi-file-pdf text-danger',
            'doc': 'bi-file-word text-primary',
            'docx': 'bi-file-word text-primary',
            'xls': 'bi-file-excel text-success',
            'xlsx': 'bi-file-excel text-success',
            'png': 'bi-file-image text-info',
            'jpg': 'bi-file-image text-info',
            'jpeg': 'bi-file-image text-info',
            'gif': 'bi-file-image text-info',
            'zip': 'bi-file-zip text-warning',
            'sql': 'bi-file-code text-secondary',
            'json': 'bi-file-code text-secondary',
            'py': 'bi-file-code text-secondary',
            'fig': 'bi-file-earmark text-purple',
        }
        return icons.get(ext, 'bi-file-earmark text-secondary')


class FileShare(models.Model):
    file = models.ForeignKey(ProjectFile, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='shared_files'
    )
    shared_by = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='files_shared_by_me'
    )
    shared_at = models.DateTimeField(auto_now_add=True)
    can_download = models.BooleanField(default=True)
    can_delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'file_shares'
        unique_together = ['file', 'shared_with']
