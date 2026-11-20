import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from apps.users.models import User
from apps.audit.models import SystemSettings

client = Client()
user = User.objects.filter(is_superuser=True).first() or User.objects.first()
client.force_login(user)

# 1. Test GET tabs
tabs = ['general', 'security', 'appearance', 'system', 'integrations', 'projects', 'notifications']
for t in tabs:
    url = f'/audit/settings/?tab={t}'
    res = client.get(url)
    assert res.status_code == 200, f"Failed GET {url}: {res.status_code}"
    print(f"OK {url} -> 200")

# 2. Test Backup Create POST
res_backup = client.post('/audit/settings/backup/create/', content_type='application/json')
assert res_backup.status_code == 200, f"Failed backup create: {res_backup.status_code}"
assert res_backup.json().get('status') == 'success', f"Invalid backup response: {res_backup.json()}"
print("OK Backup Create AJAX -> 200")

# 3. Test Backup Download GET
res_download = client.get('/audit/settings/backup/download/')
assert res_download.status_code == 200, f"Failed backup download: {res_download.status_code}"
assert 'taskwave_backup' in res_download.get('Content-Disposition', ''), "Invalid download disposition"
print("OK Backup Download -> 200")

# 4. Test Clear Cache POST
res_cache = client.post('/audit/settings/cache/clear/', content_type='application/json')
assert res_cache.status_code == 200, f"Failed clear cache: {res_cache.status_code}"
assert res_cache.json().get('status') == 'success'
print("OK Clear Cache AJAX -> 200")

# 5. Test Optimize DB POST
res_opt = client.post('/audit/settings/db/optimize/', content_type='application/json')
assert res_opt.status_code == 200, f"Failed optimize DB: {res_opt.status_code}"
assert res_opt.json().get('status') == 'success'
print("OK Optimize DB AJAX -> 200")

# 6. Test Settings Save POST
post_data = {
    'tab': 'security',
    'two_factor_auth': 'on',
    'password_expiry_days': '60',
    'max_login_attempts': '3',
    'session_timeout_minutes': '15',
}
res_save = client.post('/audit/settings/', post_data)
assert res_save.status_code == 302, f"Failed settings save POST: {res_save.status_code}"
settings_obj = SystemSettings.get_settings()
assert settings_obj.two_factor_auth is True, "2FA was not updated in DB"
assert settings_obj.password_expiry_days == 60, "Password expiry was not updated in DB"
assert settings_obj.max_login_attempts == 3, "Max login attempts was not updated in DB"
print("OK Settings Save POST -> DB verified!")

# 7. Check Content of /audit/settings/
res_main = client.get('/audit/settings/')
content = res_main.content.decode('utf-8')

expected_elements = [
    'switchSettingsTab(\'general\')',
    'switchSettingsTab(\'security\')',
    'switchSettingsTab(\'appearance\')',
    'switchSettingsTab(\'system\')',
    'switchSettingsTab(\'integrations\')',
    'tabPanel-general',
    'tabPanel-security',
    'tabPanel-appearance',
    'tabPanel-system',
    'tabPanel-integrations',
    'Backup Now',
    'Download Latest Backup',
    'Clear Cache',
    'Database Optimization',
    'Change Logo',
    'togglePasswordVisibility',
]

for elem in expected_elements:
    assert elem in content, f"Missing element in /audit/settings/: {elem}"
    print(f"Verified element: {elem}")

print("\nALL SETTINGS PAGE CHECKS PASSED SUCCESSFULLY!")

