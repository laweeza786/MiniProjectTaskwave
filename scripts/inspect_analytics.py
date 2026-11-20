import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from django.db.models import Count
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.users.models import User
from apps.departments.models import Department

today = timezone.now().date()
print("Today:", today)
upcoming = Task.objects.filter(due_date__isnull=False).exclude(status='completed').order_by('due_date')[:5]
for t in upcoming:
    days = (t.due_date - today).days
    print(t.title, t.due_date, days)

print("\nTop members:")
top_members = []
for u in User.objects.filter(is_active=True):
    completed_count = Task.objects.filter(assignees=u, status='completed').count()
    assigned_count = Task.objects.filter(assignees=u).count()
    pct = int((completed_count / assigned_count * 100)) if assigned_count > 0 else 0
    top_members.append({
        'user': u,
        'name': u.get_full_name() or u.email.split('@')[0],
        'completed_count': completed_count,
        'assigned_count': assigned_count,
        'pct': pct,
    })
top_members.sort(key=lambda x: (x['completed_count'], x['pct']), reverse=True)
for m in top_members[:5]:
    print(m)

print("\nProjects progress:")
for p in Project.objects.annotate(total_tasks_count=Count('tasks')).order_by('-total_tasks_count')[:5]:
    total = p.total_tasks_count
    completed = p.tasks.filter(status='completed').count()
    pct = int((completed / total * 100)) if total > 0 else 0
    print(p.name, completed, total, pct)
