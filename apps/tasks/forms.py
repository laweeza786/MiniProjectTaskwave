from django import forms
from apps.tasks.models import Task, Subtask, TaskComment, TaskAttachment, TaskSubmission, TaskReview
from apps.projects.models import Project
from apps.departments.models import Department
from apps.users.models import User


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'project', 'department', 'category', 'tags',
            'start_date', 'due_date', 'status', 'priority', 'visibility',
            'estimated_hours'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task Title', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Task details, requirements, acceptance criteria...'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bug, urgent, frontend, v1.0'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 8.5', 'step': '0.5'}),
        }


class SubtaskForm(forms.ModelForm):
    class Meta:
        model = Subtask
        fields = ['title', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add a subtask...', 'required': True}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write a comment or mention @team member...', 'required': True}),
        }


class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your completed work, links, or notes for the reviewer...', 'required': True}),
        }


class TaskReviewForm(forms.ModelForm):
    class Meta:
        model = TaskReview
        fields = ['decision', 'comments']
        widgets = {
            'decision': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Feedback or required changes for the submitter...'}),
        }
