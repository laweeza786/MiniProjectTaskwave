from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from apps.tasks.models import Task, Subtask
from apps.notifications.models import Notification


@login_required
@csrf_exempt
def update_task_status_api(request, task_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            task = Task.objects.get(id=task_id)
            
            # Simple permission check
            if request.user in task.assignees.all() or request.user == task.created_by or request.user.is_admin_user:
                task.status = new_status
                if new_status == 'completed':
                    task.progress = 100
                task.save()
                return JsonResponse({'success': True, 'task_id': task.id, 'status': task.status})
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
@csrf_exempt
def toggle_subtask_api(request, subtask_id):
    if request.method == 'POST':
        try:
            subtask = Subtask.objects.get(id=subtask_id)
            subtask.is_completed = not subtask.is_completed
            subtask.save()
            # update task progress
            task = subtask.task
            task.progress = task.get_subtask_progress()
            task.save()
            return JsonResponse({'success': True, 'is_completed': subtask.is_completed, 'progress': task.progress})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def mark_notification_read_api(request, notification_id):
    try:
        notif = Notification.objects.get(id=notification_id, recipient=request.user)
        notif.mark_read()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


urlpatterns = [
    path('tasks/<int:task_id>/update-status/', update_task_status_api, name='api_update_task_status'),
    path('subtasks/<int:subtask_id>/toggle/', toggle_subtask_api, name='api_toggle_subtask'),
    path('notifications/<int:notification_id>/read/', mark_notification_read_api, name='api_mark_notification_read'),
]
