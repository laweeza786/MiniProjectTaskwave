from django import forms
from apps.meetings.models import Meeting
from apps.users.models import User
import secrets


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'project', 'scheduled_start', 'scheduled_end', 'allow_screen_sharing', 'allow_chat']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Daily Standup, Sprint Review...', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Meeting agenda...'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': True}),
            'scheduled_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'allow_screen_sharing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_chat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
