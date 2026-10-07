from django import forms
from apps.departments.models import Department
from apps.users.models import User


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'head', 'email', 'phone', 'location', 'status', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department Name', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Department mission and functions...'}),
            'head': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'dept@taskwave.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 (555) 123-4567'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Floor 4, West Wing'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-laptop, bi-shield, bi-megaphone'}),
        }
