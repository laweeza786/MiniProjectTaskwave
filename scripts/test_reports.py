import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from apps.users.models import User
from apps.projects.models import Project
from apps.departments.models import Department

client = Client()
user = User.objects.filter(is_superuser=True).first() or User.objects.first()
client.force_login(user)

proj = Project.objects.first()
dept = Department.objects.first()

test_urls = [
    '/reports/',
    '/reports/?range=7d',
    '/reports/?range=30d',
    '/reports/?range=month',
    '/reports/?range=year',
    '/reports/?range=all',
    f'/reports/?project={proj.id if proj else 1}',
    f'/reports/?department={dept.id if dept else 1}',
    f'/reports/?member={user.id}',
    '/reports/?status=completed',
    '/reports/?status=in_progress',
    '/reports/?status=overdue',
    '/reports/export/tasks/',
    '/reports/export/projects/',
    '/reports/export/members/',
    '/reports/export/overtime/',
]

for url in test_urls:
    res = client.get(url)
    assert res.status_code == 200, f"Failed GET {url} with status {res.status_code}"
    print(f"OK {url} -> 200")

# Check content of main reports page
res = client.get('/reports/')
content = res.content.decode('utf-8')

expected_elements = [
    '/tasks/',
    '/tasks/?status=completed',
    '/tasks/?status=in_progress',
    '/members/?status=active',
    '/projects/',
    '/departments/',
    '/overtime/',
    'scheduleReportModal',
    'generateReportDropdown',
    'Task Completion Report',
    'Task Status Report',
    'Project Progress Report',
    'Member Performance Report',
    'Overtime Report',
    'Report Filters',
    'Apply Filters',
    'Recent Reports',
    'Export Report',
]

for elem in expected_elements:
    assert elem in content, f"Missing element in /reports/: {elem}"
    print(f"Verified element: {elem}")

print("\nALL REPORTS PAGE CHECKS PASSED SUCCESSFULLY!")

