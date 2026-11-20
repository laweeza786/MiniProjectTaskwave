import os
import sys
import django
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.notifications.models import Notification, NotificationPreference
from django.utils import timezone


def seed_notifications():
    admin = User.objects.filter(email='admin@taskwave.io').first()
    if not admin:
        print('Admin user not found!')
        return

    rahul = User.objects.filter(email='rahul@taskwave.com').first()
    priya = User.objects.filter(email='priya@taskwave.com').first()
    aman = User.objects.filter(email='aman@taskwave.com').first()
    neha = User.objects.filter(email='neha@taskwave.com').first()
    vikram = User.objects.filter(email='vikram@taskwave.com').first()

    # Clear existing notifications for admin
    admin.notifications.all().delete()
    now = timezone.now()

    sample_notifications = [
        # 1 - Tasks
        ('task_assigned', 'New Task Assigned', 'Rahul Kumar assigned you a new task "API Documentation" in project Mobile App.', False, now - timedelta(minutes=15), rahul, '/tasks/'),
        # 2 - Tasks
        ('task_completed', 'Task Completed', 'Priya Singh marked task "UI Design Review" as completed.', False, now - timedelta(minutes=45), priya, '/tasks/'),
        # 3 - Messages
        ('new_message', 'New Message', 'You have a new message from Development Team.', False, now - timedelta(hours=1, minutes=30), rahul, '/messages/'),
        # 4 - Projects
        ('project_update', 'Project Update', 'The project "College Portal" has been moved to Review stage.', False, now - timedelta(hours=3), priya, '/projects/'),
        # 5 - Tasks
        ('deadline_approaching', 'Upcoming Deadline', 'Task "Database Optimization" is due tomorrow (21 Nov 2026).', False, now - timedelta(hours=5), None, '/tasks/'),
        # 6 - Mentions
        ('mention', 'You were mentioned', 'Aman Sharma mentioned you in a comment on "Security Module".', True, now - timedelta(hours=8), aman, '/tasks/'),
        # 7 - Projects
        ('file_shared', 'New File Shared', 'Neha Tiwari shared a file "api_documentation.pdf" in project TaskWave.', True, now - timedelta(days=1), neha, '/files/'),
        # 8 - Tasks
        ('task_overdue', 'Overdue Task', 'Task "Testing and Bug Fixes" is overdue.', True, now - timedelta(days=1, hours=2), None, '/tasks/'),
        # 9 - Tasks
        ('task_assigned', 'New Task Assigned', 'Priya Singh assigned you a task "Client Review Prep" in project TaskWave API.', True, now - timedelta(days=1, hours=4), priya, '/tasks/'),
        # 10 - System
        ('system', 'System Maintenance Scheduled', 'Scheduled database maintenance on Sunday at 02:00 AM UTC.', True, now - timedelta(days=1, hours=6), None, '/settings/'),
        # 11 - Mentions
        ('mention', 'You were mentioned', 'Neha Tiwari mentioned you in "Wireframe Design feedback".', True, now - timedelta(days=2), neha, '/tasks/'),
        # 12 - Messages
        ('new_message', 'New Message from Aman Sharma', 'Can you share the API documentation when ready?', True, now - timedelta(days=2, hours=3), aman, '/messages/'),
        # 13 - Projects
        ('project_update', 'Project Milestone Reached', 'Project "TaskWave API" milestone "Alpha Release" achieved.', True, now - timedelta(days=2, hours=5), None, '/projects/'),
        # 14 - Tasks
        ('task_completed', 'Task Completed', 'Aman Sharma completed task "Database Schema Design".', True, now - timedelta(days=3), aman, '/tasks/'),
        # 15 - System
        ('system', 'Security Alert: New Sign-In', 'New sign-in detected from IP 192.168.1.18 (Chrome on Windows).', True, now - timedelta(days=3, hours=2), None, '/audit/'),
        # 16 - Tasks
        ('deadline_approaching', 'Upcoming Deadline', 'Project "Mobile App" milestone deadline in 2 days.', True, now - timedelta(days=3, hours=5), None, '/projects/'),
        # 17 - Messages
        ('new_message', 'New Message in General', 'Vikram Singh: Testing completed for module 3.', True, now - timedelta(days=4), vikram, '/messages/'),
        # 18 - Tasks
        ('task_approved', 'Task Approved', 'Your submission for "Authentication Module" was approved by Rahul Kumar.', True, now - timedelta(days=4, hours=2), rahul, '/tasks/'),
        # 19 - System
        ('member_joined', 'New Member Joined', 'Vikram Singh joined the Quality Assurance department.', True, now - timedelta(days=5), vikram, '/members/'),
        # 20 - System
        ('system', 'Backup Completed', 'Automated system backup completed successfully (2.4 GB).', True, now - timedelta(days=5, hours=3), None, '/audit/'),
        # 21 - Tasks
        ('task_assigned', 'New Task Assigned', 'Assigned to task "Setup Development Environment".', True, now - timedelta(days=6), rahul, '/tasks/'),
        # 22 - Projects
        ('file_shared', 'New File Uploaded', 'Priya Singh uploaded "Dashboard_Design.fig" in UI Design.', True, now - timedelta(days=6, hours=4), priya, '/files/'),
        # 23 - Projects
        ('project_update', 'Project Created', 'New project "Internal Tools" created by Rahul Kumar.', True, now - timedelta(days=7), rahul, '/projects/'),
        # 24 - System
        ('system', 'Welcome to TaskWave', 'Welcome to your workspace! Explore dashboard, kanban and collaborate with your team.', True, now - timedelta(days=10), None, '/'),
    ]

    for ntype, title, msg, is_read, ctime, actor, url in sample_notifications:
        n = Notification.objects.create(
            recipient=admin,
            notification_type=ntype,
            title=title,
            message=msg,
            is_read=is_read,
            actor=actor,
            url=url,
        )
        Notification.objects.filter(id=n.id).update(created_at=ctime)

    NotificationPreference.objects.get_or_create(
        user=admin,
        defaults={
            'email_notifications': True,
            'browser_notifications': True,
            'task_updates': True,
            'project_updates': True,
            'message_notifications': True,
            'overtime_notifications': True,
            'system_notifications': False,
        }
    )

    print(f'Successfully seeded {admin.notifications.count()} notifications for {admin.email}!')


if __name__ == '__main__':
    seed_notifications()
