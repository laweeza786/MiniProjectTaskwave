from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, FileResponse, JsonResponse
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
import os

from apps.files.models import ProjectFile, FileShare
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.users.models import User
from apps.audit.middleware import log_activity


def format_bytes(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


@login_required
def file_list_view(request):
    base_files = ProjectFile.objects.select_related('uploaded_by', 'project', 'task').prefetch_related('shares')

    # Top KPI Metrics
    total_files = base_files.filter(is_deleted=False).count()
    total_bytes = base_files.filter(is_deleted=False).aggregate(s=Sum('file_size'))['s'] or 0
    total_storage_display = format_bytes(total_bytes)
    shared_files_count = FileShare.objects.values('file_id').distinct().count()
    deleted_files_count = base_files.filter(is_deleted=True).count()

    # Filters
    type_filter = request.GET.get('type', '').strip().lower()
    if type_filter == 'deleted':
        files_qs = base_files.filter(is_deleted=True)
    elif type_filter == 'shared':
        shared_file_ids = FileShare.objects.values_list('file_id', flat=True)
        files_qs = base_files.filter(is_deleted=False, id__in=shared_file_ids)
    else:
        files_qs = base_files.filter(is_deleted=False)

    project_filter = request.GET.get('project', '').strip()
    if project_filter:
        if project_filter.isdigit():
            files_qs = files_qs.filter(project_id=int(project_filter))
        else:
            files_qs = files_qs.filter(project__name__iexact=project_filter)

    file_type_filter = request.GET.get('file_type', '').strip()
    if file_type_filter:
        files_qs = files_qs.filter(file_type__iexact=file_type_filter)

    member_filter = request.GET.get('member', '').strip()
    if member_filter:
        if member_filter.isdigit():
            files_qs = files_qs.filter(uploaded_by_id=int(member_filter))
        else:
            files_qs = files_qs.filter(
                Q(uploaded_by__first_name__icontains=member_filter) |
                Q(uploaded_by__last_name__icontains=member_filter)
            )

    query = request.GET.get('q', '').strip()
    if query:
        files_qs = files_qs.filter(
            Q(name__icontains=query) |
            Q(original_filename__icontains=query) |
            Q(project__name__icontains=query)
        )

    # Project Folders Data
    folder_colors = {
        'TaskWave API': ('#fef3c7', '#d97706'),
        'Mobile App': ('#e0f2fe', '#0284c7'),
        'UI Design': ('#dcfce7', '#16a34a'),
        'Documentation': ('#f3e8ff', '#9333ea'),
        'QA & Testing': ('#ffedd5', '#ea580c'),
    }

    all_projects = Project.objects.all().order_by('name')
    project_folders = []
    for p in all_projects:
        p_files = p.files.filter(is_deleted=False)
        p_count = p_files.count()
        p_size = p_files.aggregate(s=Sum('file_size'))['s'] or 0
        bg_color, icon_color = folder_colors.get(p.name, ('#f1f5f9', '#475569'))
        project_folders.append({
            'id': p.id,
            'name': p.name,
            'files_count': p_count,
            'size_display': format_bytes(p_size),
            'bg_color': bg_color,
            'icon_color': icon_color,
            'is_selected': (project_filter == str(p.id) or project_filter.lower() == p.name.lower()),
        })

    # View Mode (list vs grid)
    view_mode = request.GET.get('view', 'list').strip().lower()
    if view_mode not in ['list', 'grid']:
        view_mode = 'list'

    # Pagination
    try:
        per_page = int(request.GET.get('per_page', 10))
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(files_qs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # First file for preview drawer default
    first_file = page_obj[0] if page_obj else None

    # Available File Types and Active Members
    all_file_types = ['PDF', 'SQL', 'FIG', 'DOCX', 'XLSX', 'ZIP', 'PNG', 'JPG']
    all_members = User.objects.filter(is_active=True).order_by('first_name', 'last_name')

    context = {
        'page_obj': page_obj,
        'files': page_obj.object_list,
        'first_file': first_file,
        'total_files': total_files,
        'total_storage_display': total_storage_display,
        'shared_files_count': shared_files_count,
        'deleted_files_count': deleted_files_count,
        'project_folders': project_folders,
        'projects': all_projects,
        'all_file_types': all_file_types,
        'all_members': all_members,
        'selected_type': type_filter or 'all',
        'selected_project': project_filter,
        'selected_file_type': file_type_filter,
        'selected_member': member_filter,
        'view_mode': view_mode,
        'per_page': per_page,
        'q': query,
        'total_filtered_count': files_qs.count(),
    }
    return render(request, 'files/file_list.html', context)


@login_required
def file_upload_view(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('file') or request.FILES.getlist('files')
        if not uploaded_files and request.FILES.get('file'):
            uploaded_files = [request.FILES['file']]

        project_id = request.POST.get('project') or None
        if project_id and project_id.isdigit():
            project = Project.objects.filter(id=int(project_id)).first()
        elif project_id:
            project = Project.objects.filter(name__iexact=project_id).first()
        else:
            project = None

        count = 0
        for uploaded in uploaded_files:
            ext = uploaded.name.split('.')[-1].upper() if '.' in uploaded.name else 'FILE'
            f = ProjectFile.objects.create(
                name=uploaded.name,
                original_filename=uploaded.name,
                file=uploaded,
                file_type=ext,
                file_size=uploaded.size,
                project=project,
                uploaded_by=request.user,
                is_deleted=False
            )
            count += 1
            log_activity(request.user, 'uploaded', 'Files', object_type='ProjectFile', object_id=f.id, object_repr=f.name, request=request)

        if count > 0:
            messages.success(request, f'{count} file(s) uploaded successfully!')
        else:
            messages.error(request, 'Please select a file to upload.')

    return redirect('files:list')


@login_required
def folder_create_view(request):
    if request.method == 'POST':
        folder_name = request.POST.get('folder_name', '').strip()
        description = request.POST.get('description', '').strip()
        if not folder_name:
            messages.error(request, 'Folder name is required.')
            return redirect('files:list')

        # Check if project folder already exists
        p, created = Project.objects.get_or_create(
            name=folder_name,
            defaults={
                'project_key': f"P-{abs(hash(folder_name)) % 10000}",
                'description': description or f"Folder for {folder_name} documents.",
                'status': 'active'
            }
        )
        log_activity(request.user, 'created', 'Files', object_type='Folder', object_id=p.id, object_repr=p.name, request=request)
        messages.success(request, f'Folder "{p.name}" created successfully!')
    return redirect('files:list')


@login_required
def file_download_view(request, pk):
    file_obj = get_object_or_404(ProjectFile, pk=pk)
    if not file_obj.file:
        raise Http404('File not found.')

    try:
        response = FileResponse(file_obj.file.open('rb'), as_attachment=True, filename=file_obj.original_filename)
        log_activity(request.user, 'downloaded', 'Files', object_type='ProjectFile', object_id=file_obj.id, object_repr=file_obj.name, request=request)
        return response
    except Exception as e:
        messages.error(request, f'Could not download file: {str(e)}')
        return redirect('files:list')


@login_required
def file_delete_view(request, pk):
    file_obj = get_object_or_404(ProjectFile, pk=pk)
    if file_obj.is_deleted:
        # Permanent delete
        file_obj.delete()
        messages.success(request, f'File "{file_obj.name}" permanently deleted.')
    else:
        file_obj.is_deleted = True
        file_obj.deleted_at = timezone.now()
        file_obj.save()
        log_activity(request.user, 'deleted', 'Files', object_type='ProjectFile', object_id=file_obj.id, object_repr=file_obj.name, request=request)
        messages.success(request, f'File "{file_obj.name}" moved to trash.')

    return redirect('files:list')


@login_required
def file_restore_view(request, pk):
    file_obj = get_object_or_404(ProjectFile, pk=pk)
    file_obj.is_deleted = False
    file_obj.deleted_at = None
    file_obj.save()
    log_activity(request.user, 'updated', 'Files', object_type='ProjectFile', object_id=file_obj.id, object_repr=f'Restored {file_obj.name}', request=request)
    messages.success(request, f'File "{file_obj.name}" restored successfully!')
    return redirect('files:list')


@login_required
def file_rename_view(request, pk):
    file_obj = get_object_or_404(ProjectFile, pk=pk)
    if request.method == 'POST':
        new_name = request.POST.get('new_name', '').strip()
        if new_name:
            file_obj.name = new_name
            file_obj.save()
            log_activity(request.user, 'updated', 'Files', object_type='ProjectFile', object_id=file_obj.id, object_repr=f'Renamed to {new_name}', request=request)
            messages.success(request, f'File renamed to "{new_name}".')
        else:
            messages.error(request, 'File name cannot be empty.')
    return redirect('files:list')


@login_required
def file_share_view(request, pk):
    file_obj = get_object_or_404(ProjectFile, pk=pk)
    if request.method == 'POST':
        user_ids = request.POST.getlist('users')
        if user_ids:
            for uid in user_ids:
                if uid.isdigit():
                    u = User.objects.filter(id=int(uid)).first()
                    if u and u != request.user:
                        FileShare.objects.get_or_create(
                            file=file_obj,
                            shared_with=u,
                            defaults={'shared_by': request.user, 'can_download': True}
                        )
            log_activity(request.user, 'shared', 'Files', object_type='ProjectFile', object_id=file_obj.id, object_repr=f'Shared {file_obj.name}', request=request)
            messages.success(request, f'File "{file_obj.name}" shared successfully!')
        else:
            messages.error(request, 'Please select members to share with.')
    return redirect('files:list')
