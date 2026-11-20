import os
import sys
from decimal import Decimal
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.users.models import User
from apps.departments.models import Department
from apps.overtime.models import OvertimeRequest

today = timezone.now().date()
users = list(User.objects.filter(is_active=True))
projects = list(Project.objects.all())
tasks = list(Task.objects.all())
departments = list(Department.objects.all())

# Add some realistic overtime records if count < 6
if OvertimeRequest.objects.count() < 6:
    ot_data = [
        (users[0], projects[0] if projects else None, 'Database migration overtime work', Decimal('5.0'), 'approved', today - timedelta(days=2)),
        (users[1] if len(users) > 1 else users[0], projects[1] if len(projects) > 1 else None, 'Critical bug fix deployment', Decimal('4.5'), 'approved', today - timedelta(days=5)),
        (users[2] if len(users) > 2 else users[0], projects[0] if projects else None, 'API documentation sprint', Decimal('6.0'), 'pending', today - timedelta(days=1)),
        (users[3] if len(users) > 3 else users[0], None, 'Weekend server maintenance', Decimal('8.0'), 'approved', today - timedelta(days=8)),
        (users[4] if len(users) > 4 else users[0], projects[0] if projects else None, 'Unapproved extra feature work', Decimal('2.0'), 'rejected', today - timedelta(days=4)),
        (users[0], projects[0] if projects else None, 'System load testing run', Decimal('4.0'), 'approved', today - timedelta(days=12)),
    ]
    for emp, proj, desc, hrs, stat, dt in ot_data:
        OvertimeRequest.objects.create(
            employee=emp,
            project=proj,
            task=tasks[0] if tasks else None,
            description=desc,
            department=emp.department if hasattr(emp, 'department') and emp.department else (departments[0] if departments else None),
            start_date=dt,
            end_date=dt,
            requested_hours=hrs,
            approved_hours=hrs if stat == 'approved' else Decimal('0.0'),
            hourly_rate=Decimal('25.00'),
            status=stat
        )
    print("Added overtime records. New count:", OvertimeRequest.objects.count())
else:
    print("Overtime records already sufficient:", OvertimeRequest.objects.count())

