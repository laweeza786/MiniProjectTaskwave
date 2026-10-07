from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.overtime.models import OvertimeRequest
from apps.overtime.forms import OvertimeRequestForm
from apps.audit.middleware import log_activity


@login_required
def overtime_list_view(request):
    user = request.user
    is_approver = user.is_superuser or (user.role and user.role.name in ['Administrator', 'Project Manager', 'Team Lead'])

    if is_approver:
        requests_list = OvertimeRequest.objects.select_related('employee', 'department', 'project').all()
    else:
        requests_list = OvertimeRequest.objects.filter(employee=user).select_related('department', 'project')

    status_filter = request.GET.get('status')
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)

    form = OvertimeRequestForm()

    context = {
        'requests': requests_list,
        'form': form,
        'is_approver': is_approver,
        'pending_count': requests_list.filter(status='pending').count(),
    }
    return render(request, 'overtime/overtime_list.html', context)


@login_required
def overtime_create_view(request):
    if request.method == 'POST':
        form = OvertimeRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.employee = request.user
            req.status = 'pending'
            req.save()
            log_activity(request.user, 'created', 'Overtime', object_type='OvertimeRequest', object_id=req.id, object_repr=f'{req.requested_hours}h on {req.start_date}', request=request)
            messages.success(request, 'Overtime request submitted for approval.')
    return redirect('overtime:list')


@login_required
def overtime_decision_view(request, pk, decision):
    if not (request.user.is_superuser or (request.user.role and request.user.role.name in ['Administrator', 'Project Manager'])):
        messages.error(request, 'Permission denied.')
        return redirect('overtime:list')

    req = get_object_or_404(OvertimeRequest, pk=pk)
    if decision in ['approve', 'reject']:
        req.status = 'approved' if decision == 'approve' else 'rejected'
        if req.status == 'approved':
            req.approved_hours = req.requested_hours
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.save()

        log_activity(request.user, req.status, 'Overtime', object_type='OvertimeRequest', object_id=req.id, object_repr=f'Overtime {req.status}', request=request)
        messages.success(request, f'Overtime request {req.status}.')

    return redirect('overtime:list')
