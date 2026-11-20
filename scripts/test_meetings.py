import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from apps.users.models import User
from apps.meetings.models import Meeting

client = Client()
user = User.objects.filter(is_superuser=True).first() or User.objects.first()
client.force_login(user)

# 1. Test List & Filter URLs
urls_to_test = [
    '/meetings/',
    '/meetings/?status=scheduled',
    '/meetings/?status=ongoing',
    '/meetings/?status=completed',
]

for url in urls_to_test:
    res = client.get(url)
    assert res.status_code == 200, f"Failed GET {url}: status {res.status_code}"
    print(f"OK {url} -> 200")

# 2. Test Instant Meeting
res_instant = client.get('/meetings/instant/')
assert res_instant.status_code == 302, f"Failed instant meeting redirect: {res_instant.status_code}"
target_room_url = res_instant['Location']
print(f"Instant meeting redirected to: {target_room_url}")
res_room = client.get(target_room_url)
assert res_room.status_code == 200, f"Failed room load: {res_room.status_code}"
print(f"Room loaded OK: {target_room_url} -> 200")

# 3. Test Create Meeting POST
post_data = {
    'title': 'Automated Test Sync Conference',
    'description': 'Discussion on automated test verification',
    'scheduled_start': '2026-12-01T15:00',
    'participants': [user.id]
}
res_create = client.post('/meetings/create/', post_data)
assert res_create.status_code == 302, f"Failed create meeting POST: {res_create.status_code}"
assert Meeting.objects.filter(title='Automated Test Sync Conference').exists(), "Meeting was not saved in database!"
print("Meeting created successfully in DB -> 302 redirect")

# 4. Test Update Settings
res_settings = client.post('/meetings/update-settings/', {'setting': 'Allow Screen Sharing', 'value': 'true'})
assert res_settings.status_code == 200, f"Settings update failed: {res_settings.status_code}"
assert res_settings.json().get('status') == 'success', f"Settings JSON invalid: {res_settings.json()}"
print("Settings update AJAX OK -> 200")

# 5. Check Content of /meetings/
res_main = client.get('/meetings/')
content = res_main.content.decode('utf-8')

expected_elements = [
    'Video Meetings',
    'Schedule Meeting',
    'Start Instant Meeting',
    '/meetings/instant/',
    'Total Meetings',
    'Scheduled',
    'Ongoing',
    'Completed',
    'Upcoming Meetings',
    'Recent Meetings',
    'Meeting Tools',
    'Meeting Settings',
    'Participants',
    'Chat',
    'Join',
    'View',
    'scheduleMeetingModal',
]

for elem in expected_elements:
    assert elem in content, f"Missing element in /meetings/: {elem}"
    print(f"Verified element: {elem}")

print("\nALL MEETINGS PAGE CHECKS PASSED SUCCESSFULLY!")

