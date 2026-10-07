from django import forms
from apps.overtime.models import OvertimeRequest


class OvertimeRequestForm(forms.ModelForm):
    class Meta:
        model = OvertimeRequest
        fields = ['project', 'task', 'department', 'start_date', 'end_date', 'start_time', 'end_time', 'requested_hours', 'description']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'task': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'requested_hours': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 4.0', 'step': '0.5', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Justification for overtime work...', 'required': True}),
        }
