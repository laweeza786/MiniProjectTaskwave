import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from apps.users.models import User

client = Client()
user = User.objects.filter(is_superuser=True).first() or User.objects.first()
client.force_login(user)

routes_to_verify = [
    ('/', 'Dashboard (Core)'),
    ('/projects/', 'Projects List'),
    ('/projects/create/', 'Projects Create Form'),
    ('/tasks/', 'Tasks List'),
    ('/tasks/create/', 'Tasks Create Form'),
    ('/kanban/', 'Kanban Board'),
    ('/calendar/', 'Calendar View'),
    ('/members/', 'Members List'),
    ('/members/roles/', 'Roles & Permissions'),
    ('/departments/', 'Departments List'),
    ('/audit/logs/', 'Activity Logs'),
    ('/audit/settings/', 'System Settings'),
    ('/files/', 'File Management'),
    ('/messages/', 'Real-time Messaging'),
    ('/notifications/', 'Notifications & Preferences'),
    ('/analytics/', 'Analytics Dashboard'),
    ('/overtime/', 'Overtime Management'),
    ('/reports/', 'Reports & Exports'),
    ('/meetings/', 'Video Meetings'),
]

failed = []
passed = []

for route, name in routes_to_verify:
    try:
        res = client.get(route)
        if res.status_code in [200, 302]:
            passed.append((route, name, res.status_code))
            print(f"[PASS] {name} ({route}) -> HTTP {res.status_code}")
        else:
            failed.append((route, name, res.status_code))
            print(f"[FAIL] {name} ({route}) -> HTTP {res.status_code}")
    except Exception as e:
        failed.append((route, name, str(e)))
        print(f"[ERROR] {name} ({route}) -> {e}")

print("\n" + "="*50)
print(f"Total Routes Checked: {len(routes_to_verify)}")
print(f"Passed: {len(passed)}")
print(f"Failed: {len(failed)}")
print("="*50)

if failed:
    sys.exit(1)
print("ALL SYSTEM MODULES OPERATIONAL!")

