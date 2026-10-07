from django import forms
from apps.projects.models import Project, ProjectMilestone, ProjectMember
from apps.departments.models import Department
from apps.users.models import User


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'department', 'manager', 'start_date', 'end_date',
            'priority', 'status', 'category', 'visibility', 'goals', 'tags', 'client', 'color'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Name', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe project scope and goals...'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Key milestones and objectives'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Frontend, UI/UX, React, Django (comma-separated)'}),
            'client': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client or stakeholder name'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }


class ProjectMilestoneForm(forms.ModelForm):
    class Meta:
        model = ProjectMilestone
        fields = ['title', 'due_date', 'is_completed']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Milestone Title'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
