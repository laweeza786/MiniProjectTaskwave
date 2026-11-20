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
user = User.objects.filter(email='admin@taskwave.io').first()
if not user:
    user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.first()

client.force_login(user)

ranges = ['', '?range=7d', '?range=30d', '?range=month', '?range=year', '?range=all']
for r in ranges:
    url = f'/analytics/{r}'
    resp = client.get(url)
    assert resp.status_code == 200, f"Failed for {url}: status {resp.status_code}"
    print(f"OK {url} -> 200")

# Verify HTML content of main analytics page
resp = client.get('/analytics/')
content = resp.content.decode('utf-8')

expected_snippets = [
    '/tasks/',
    '/tasks/?status=completed',
    '/tasks/?status=in_progress',
    '/members/?status=active',
    '/projects/?status=active',
    '/members/',
    '/projects/',
    'dash-kpi-card',
    'Task Completion Overview',
    'Task Status Distribution',
    'Top Performing Members',
    'Projects Progress',
    'Upcoming Deadlines',
    'Last 30 Days',
    'Last 7 Days',
    'This Month',
    'This Year',
]

for s in expected_snippets:
    assert s in content, f"Missing snippet in /analytics/: {s}"
    print(f"Snippet verified: {s}")

# Verify target URLs return 200
target_urls = [
    '/tasks/',
    '/tasks/?status=completed',
    '/tasks/?status=in_progress',
    '/members/?status=active',
    '/projects/?status=active',
    '/members/',
    '/projects/',
]

for u in target_urls:
    r = client.get(u)
    assert r.status_code == 200, f"Target URL failed {u}: {r.status_code}"
    print(f"Target URL OK: {u} -> 200")

print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

