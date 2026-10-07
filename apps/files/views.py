from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from apps.files.models import ProjectFile, FileShare
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.users.models import User
from apps.audit.middleware import log_activity


@login_required
def file_list_view(request):
    files = ProjectFile.objects.filter(is_deleted=False).select_related('uploaded_by', 'project', 'task')
    projects = Project.objects.all()

    project_filter = request.GET.get('project')
    if project_filter:
        files = files.filter(project_id=project_filter)

    query = request.GET.get('q', '').strip()
    if query:
        files = files.filter(name__icontains=query)

    return render(request, 'files/file_list.html', {
        'files': files,
        'projects': projects,
        'total_files': files.count(),
        'all_users': User.objects.filter(is_active=True).exclude(id=request.user.id),
    })


@login_required
def file_upload_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded = request.FILES['file']
        project_id = request.POST.get('project') or None
        task_id = request.POST.get('task') or None

        f = ProjectFile.objects.create(
            name=uploaded.name,
            original_filename=uploaded.name,
            file=uploaded,
            file_size=uploaded.size,
            project_id=project_id,
            task_id=task_id,
            uploaded_by=request.user
        )
        log_activity(request.user, 'uploaded', 'Files', object_type='ProjectFile', object_id=f.id, object_repr=f.name, request=request)
        messages.success(request, f'File "{uploaded.name}" uploaded successfully!')
    return redirect('files:list')


@login_required
def file_delete_view(request, pk):
    file_obj = get_object_or_404(ProjectFile, pk=pk)
    if request.user == file_obj.uploaded_by or request.user.is_admin_user:
        file_obj.is_deleted = True
        file_obj.save()
        log_activity(request.user, 'deleted', 'Files', object_type='ProjectFile', object_id=file_obj.id, object_repr=file_obj.name, request=request)
        messages.success(request, 'File moved to trash.')
    else:
        messages.error(request, 'Permission denied.')
    return redirect('files:list')
