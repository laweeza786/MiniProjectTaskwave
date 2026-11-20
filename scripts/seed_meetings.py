import os
import sys
import secrets
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from apps.meetings.models import Meeting, MeetingParticipant
from apps.users.models import User
from apps.projects.models import Project

now = timezone.now()
users = list(User.objects.filter(is_active=True))
admin_user = User.objects.filter(is_superuser=True).first() or users[0]
projects = list(Project.objects.all())

# Clear existing meetings if any
Meeting.objects.all().delete()

meetings_data = [
    # Ongoing meetings
    {
        'title': 'Project Review - TaskWave',
        'description': 'Sprint review of core features, review of frontend dashboards and analytics integration.',
        'host': admin_user,
        'project': projects[0] if projects else None,
        'scheduled_start': now - timedelta(minutes=25),
        'scheduled_end': now + timedelta(minutes=35),
        'status': 'ongoing',
        'meeting_id': 'TW-REVIEW-101',
        'participant_count': 10,
    },
    {
        'title': 'UI/UX Design Alignment',
        'description': 'Review of design tokens, Figma handoff, and component library styling.',
        'host': users[1] if len(users) > 1 else admin_user,
        'project': projects[1] if len(projects) > 1 else None,
        'scheduled_start': now - timedelta(minutes=10),
        'scheduled_end': now + timedelta(minutes=50),
        'status': 'ongoing',
        'meeting_id': 'TW-DESIGN-102',
        'participant_count': 6,
    },

    # Scheduled (upcoming) meetings
    {
        'title': 'Development Sync & Architecture',
        'description': 'API architecture discussion, database indexes, and WebSocket connection strategies.',
        'host': users[2] if len(users) > 2 else admin_user,
        'project': projects[0] if projects else None,
        'scheduled_start': now + timedelta(hours=3),
        'scheduled_end': now + timedelta(hours=4),
        'status': 'scheduled',
        'meeting_id': 'TW-DEV-103',
        'participant_count': 9,
    },
    {
        'title': 'Client Requirement Discussion',
        'description': 'Meeting with client representatives to finalize project milestone deliveries.',
        'host': admin_user,
        'project': projects[2] if len(projects) > 2 else None,
        'scheduled_start': now + timedelta(days=1, hours=2),
        'scheduled_end': now + timedelta(days=1, hours=3),
        'status': 'scheduled',
        'meeting_id': 'TW-CLIENT-104',
        'participant_count': 5,
    },
    {
        'title': 'Sprint Planning & Backlog Grooming',
        'description': 'Assigning user stories, estimating story points, and task wave prioritization.',
        'host': users[3] if len(users) > 3 else admin_user,
        'project': projects[0] if projects else None,
        'scheduled_start': now + timedelta(days=2, hours=1),
        'scheduled_end': now + timedelta(days=2, hours=2),
        'status': 'scheduled',
        'meeting_id': 'TW-PLAN-105',
        'participant_count': 7,
    },
    {
        'title': 'Security Audit & Vulnerability Assessment',
        'description': 'Review penetration testing findings and authorization policies.',
        'host': admin_user,
        'project': projects[0] if projects else None,
        'scheduled_start': now + timedelta(days=3, hours=4),
        'scheduled_end': now + timedelta(days=3, hours=5),
        'status': 'scheduled',
        'meeting_id': 'TW-SEC-106',
        'participant_count': 4,
    },
    {
        'title': 'QA Test Automation Framework Kickoff',
        'description': 'Cypress & Selenium test suite setup for continuous deployment pipeline.',
        'host': users[4] if len(users) > 4 else admin_user,
        'project': projects[1] if len(projects) > 1 else None,
        'scheduled_start': now + timedelta(days=4, hours=2),
        'scheduled_end': now + timedelta(days=4, hours=3),
        'status': 'scheduled',
        'meeting_id': 'TW-QA-107',
        'participant_count': 6,
    },
    {
        'title': 'Marketing & Product Launch Alignment',
        'description': 'Coordination with marketing department on press release and documentation.',
        'host': users[0],
        'project': projects[0] if projects else None,
        'scheduled_start': now + timedelta(days=5, hours=3),
        'scheduled_end': now + timedelta(days=5, hours=4),
        'status': 'scheduled',
        'meeting_id': 'TW-MKT-108',
        'participant_count': 8,
    },

    # Completed (recent) meetings
    {
        'title': 'Development Team Sync',
        'description': 'Weekly development check-in and blocker removal.',
        'host': admin_user,
        'project': projects[0] if projects else None,
        'scheduled_start': now - timedelta(days=2, hours=4),
        'scheduled_end': now - timedelta(days=2, hours=3),
        'status': 'completed',
        'meeting_id': 'TW-DEV-SYNC-099',
        'participant_count': 8,
    },
    {
        'title': 'Design Review & Prototype Testing',
        'description': 'User feedback testing on new kanban and calendar interfaces.',
        'host': users[1] if len(users) > 1 else admin_user,
        'project': projects[1] if len(projects) > 1 else None,
        'scheduled_start': now - timedelta(days=3, hours=6),
        'scheduled_end': now - timedelta(days=3, hours=5),
        'status': 'completed',
        'meeting_id': 'TW-DSGN-098',
        'participant_count': 6,
    },
    {
        'title': 'Client Discussion - Phase 1 Approval',
        'description': 'Client sign-off on Phase 1 features and milestones.',
        'host': admin_user,
        'project': projects[2] if len(projects) > 2 else None,
        'scheduled_start': now - timedelta(days=4, hours=3),
        'scheduled_end': now - timedelta(days=4, hours=2),
        'status': 'completed',
        'meeting_id': 'TW-CLNT-097',
        'participant_count': 5,
    },
    {
        'title': 'Sprint Retrospective & Lessons Learned',
        'description': 'Retrospective discussion on velocity and team performance.',
        'host': users[2] if len(users) > 2 else admin_user,
        'project': projects[0] if projects else None,
        'scheduled_start': now - timedelta(days=5, hours=2),
        'scheduled_end': now - timedelta(days=5, hours=1),
        'status': 'completed',
        'meeting_id': 'TW-RETRO-096',
        'participant_count': 7,
    },
    {
        'title': 'Infrastructure Cloud Migration Review',
        'description': 'Post-migration health check and AWS instance rightsizing.',
        'host': admin_user,
        'project': projects[0] if projects else None,
        'scheduled_start': now - timedelta(days=6, hours=5),
        'scheduled_end': now - timedelta(days=6, hours=4),
        'status': 'completed',
        'meeting_id': 'TW-INFRA-095',
        'participant_count': 4,
    },
    {
        'title': 'Monthly All-Hands Team Assembly',
        'description': 'Company-wide town hall, roadmap announcements, and Q&A session.',
        'host': admin_user,
        'project': None,
        'scheduled_start': now - timedelta(days=8, hours=3),
        'scheduled_end': now - timedelta(days=8, hours=2),
        'status': 'completed',
        'meeting_id': 'TW-ALLHANDS-094',
        'participant_count': 18,
    },
]

for m_dict in meetings_data:
    p_cnt = m_dict.pop('participant_count')
    m = Meeting.objects.create(
        **m_dict,
        meeting_link=f"/meetings/room/{m_dict['meeting_id']}/",
        allow_screen_sharing=True,
        allow_recording=True,
        auto_mute_on_join=False,
        allow_chat=True,
        allow_file_sharing=True
    )
    # Add host
    MeetingParticipant.objects.get_or_create(meeting=m, user=m.host)
    # Add participants
    for u in users[:p_cnt]:
        MeetingParticipant.objects.get_or_create(meeting=m, user=u)

print("Seeded meetings successfully! Total:", Meeting.objects.count())
print("Scheduled:", Meeting.objects.filter(status='scheduled').count())
print("Ongoing:", Meeting.objects.filter(status='ongoing').count())
print("Completed:", Meeting.objects.filter(status='completed').count())

