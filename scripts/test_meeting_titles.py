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

# 1. Test ?status=completed
res_completed = client.get('/meetings/?status=completed')
assert res_completed.status_code == 200
content_completed = res_completed.content.decode('utf-8')
assert 'Completed Meetings' in content_completed, "Missing 'Completed Meetings' title"
assert 'Upcoming Meetings' not in content_completed, "Should NOT contain 'Upcoming Meetings' when viewing completed meetings"
assert 'View' in content_completed, "Completed meetings should have 'View' button"
print("OK /meetings/?status=completed verified: shows 'Completed Meetings' and NOT 'Upcoming Meetings'")

# 2. Test ?status=all
res_all = client.get('/meetings/?status=all')
assert res_all.status_code == 200
content_all = res_all.content.decode('utf-8')
assert 'All Meetings' in content_all, "Missing 'All Meetings' title"
assert 'Upcoming Meetings' not in content_all, "Should NOT contain 'Upcoming Meetings' when viewing all meetings"
print("OK /meetings/?status=all verified: shows 'All Meetings' and NOT 'Upcoming Meetings'")

# 3. Test ?status=scheduled
res_scheduled = client.get('/meetings/?status=scheduled')
assert res_scheduled.status_code == 200
content_scheduled = res_scheduled.content.decode('utf-8')
assert 'Scheduled Meetings' in content_scheduled, "Missing 'Scheduled Meetings' title"
print("OK /meetings/?status=scheduled verified: shows 'Scheduled Meetings'")

# 4. Test ?status=ongoing
res_ongoing = client.get('/meetings/?status=ongoing')
assert res_ongoing.status_code == 200
content_ongoing = res_ongoing.content.decode('utf-8')
assert 'Ongoing Meetings' in content_ongoing, "Missing 'Ongoing Meetings' title"
print("OK /meetings/?status=ongoing verified: shows 'Ongoing Meetings'")

# 5. Test default /meetings/
res_default = client.get('/meetings/')
assert res_default.status_code == 200
content_default = res_default.content.decode('utf-8')
assert 'Upcoming Meetings' in content_default, "Default should show 'Upcoming Meetings' for upcoming active meetings"
print("OK /meetings/ verified: shows 'Upcoming Meetings'")

print("\nALL DYNAMIC TITLE & FILTER TESTS PASSED SUCCESSFULLY!")

