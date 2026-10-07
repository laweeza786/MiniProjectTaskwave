"""
TaskWave - Seed Data Management Command
Populates the database with realistic development data:
- Roles & Permissions
- Departments (Engineering, Design, Marketing, Product, QA)
- Users across all roles (Admin, PM, Team Lead, Employee, Viewer)
- Projects with milestones and members
- Tasks with subtasks, comments, attachments, submissions, and status history
- Meetings and attendees
- Overtime requests
- Notifications
- System Settings
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from apps.users.models import User, Role, Permission
from apps.departments.models import Department
from apps.projects.models import Project, ProjectMember, ProjectMilestone
from apps.tasks.models import (
    Task, TaskCategory, TaskAssignee, Subtask, TaskComment,
    TaskSubmission, TaskReview, TaskStatusHistory
)
from apps.calendar_app.models import CalendarEvent
from apps.overtime.models import OvertimeRequest
from apps.messaging.models import Conversation, ConversationMember, Message
from apps.notifications.models import Notification, NotificationPreference
from apps.audit.models import SystemSettings, ActivityLog
from apps.files.models import ProjectFile


class Command(BaseCommand):
    help = 'Seeds database with realistic data for TaskWave'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Starting TaskWave database seeding...'))

        # 1. System Settings
        settings, _ = SystemSettings.objects.get_or_create(
            pk=1,
            defaults={
                'org_name': 'TaskWave Solutions Inc.',
                'org_email': 'contact@taskwave.io',
                'org_phone': '+1 (555) 928-3928',
                'primary_color': '#b45309',
                'theme': 'light'
            }
        )

        # 2. Permissions & Roles
        perm_data = [
            ('view_dashboard', 'View Dashboard', 'Dashboard'),
            ('manage_projects', 'Manage Projects', 'Projects'),
            ('manage_tasks', 'Manage Tasks', 'Tasks'),
            ('manage_kanban', 'Manage Kanban Board', 'Kanban'),
            ('manage_calendar', 'Manage Calendar Events', 'Calendar'),
            ('view_members', 'View Team Members', 'Members'),
            ('manage_departments', 'Manage Departments', 'Departments'),
            ('send_messages', 'Send Messages & Chat', 'Messaging'),
            ('view_notifications', 'View Notifications', 'Notifications'),
            ('view_analytics', 'View Analytics & Metrics', 'Analytics'),
            ('manage_overtime', 'Manage Overtime Requests', 'Overtime'),
            ('generate_reports', 'Generate Reports & Exports', 'Reports'),
            ('manage_files', 'Manage File Repository', 'Files'),
            ('manage_meetings', 'Manage Meetings & Video', 'Meetings'),
            ('manage_users', 'Manage User Accounts', 'Administration'),
            ('manage_roles', 'Manage Roles & Permissions', 'Administration'),
            ('view_audit_logs', 'View Audit & Activity Logs', 'Administration'),
            ('manage_settings', 'Manage System Settings', 'Administration'),
        ]

        permissions = {}
        for codename, name, module in perm_data:
            p, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={'name': name, 'module': module}
            )
            permissions[codename] = p

        role_configs = {
            'Administrator': list(permissions.values()),
            'Project Manager': [
                permissions['view_dashboard'], permissions['manage_projects'], permissions['manage_tasks'],
                permissions['manage_kanban'], permissions['manage_calendar'], permissions['view_members'],
                permissions['manage_departments'], permissions['send_messages'], permissions['view_notifications'],
                permissions['view_analytics'], permissions['manage_overtime'], permissions['generate_reports'],
                permissions['manage_files'], permissions['manage_meetings']
            ],
            'Team Lead': [
                permissions['view_dashboard'], permissions['manage_tasks'], permissions['manage_kanban'],
                permissions['manage_calendar'], permissions['view_members'], permissions['send_messages'],
                permissions['view_notifications'], permissions['view_analytics'], permissions['manage_overtime'],
                permissions['manage_files'], permissions['manage_meetings']
            ],
            'Employee': [
                permissions['view_dashboard'], permissions['manage_tasks'], permissions['manage_kanban'],
                permissions['manage_calendar'], permissions['view_members'], permissions['send_messages'],
                permissions['view_notifications'], permissions['manage_overtime'], permissions['manage_files'],
                permissions['manage_meetings']
            ],
            'Viewer': [
                permissions['view_dashboard'], permissions['view_members'], permissions['view_notifications']
            ]
        }

        roles = {}
        for role_name, perms in role_configs.items():
            r, _ = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': f'Default {role_name} role with assigned permissions.'}
            )
            r.permissions.set(perms)
            roles[role_name] = r

        # 3. Departments
        departments_data = [
            ('Engineering', 'Software development, infrastructure, and technical operations.', 'bi-laptop', 'eng@taskwave.io'),
            ('UI/UX Design', 'Product design, user research, wireframing, and visual assets.', 'bi-palette', 'design@taskwave.io'),
            ('Product Management', 'Product vision, sprint backlogs, and stakeholder requirements.', 'bi-kanban', 'product@taskwave.io'),
            ('Quality Assurance', 'Automated and manual testing, compliance, and bug tracking.', 'bi-check2-circle', 'qa@taskwave.io'),
            ('Marketing & Sales', 'Brand management, growth analytics, and outreach.', 'bi-megaphone', 'marketing@taskwave.io'),
        ]

        departments = {}
        for name, desc, icon, email in departments_data:
            dept, _ = Department.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'icon': icon, 'email': email, 'status': 'active'}
            )
            departments[name] = dept

        # 4. Users (Password: TaskWave2026!)
        default_pwd = 'TaskWave2026!'
        users_seed = [
            ('admin@taskwave.io', 'Alex', 'Morgan', 'Administrator', 'Engineering', 'EMP-001', '+1 555-100-001', 'Python, Django, System Architecture, AWS'),
            ('pm.sarah@taskwave.io', 'Sarah', 'Jenkins', 'Project Manager', 'Product Management', 'EMP-002', '+1 555-100-002', 'Scrum, Agile, Roadmap, Jira'),
            ('lead.david@taskwave.io', 'David', 'Kim', 'Team Lead', 'Engineering', 'EMP-003', '+1 555-100-003', 'React, TypeScript, Django, GraphQL'),
            ('design.elena@taskwave.io', 'Elena', 'Rostova', 'Employee', 'UI/UX Design', 'EMP-004', '+1 555-100-004', 'Figma, UI/UX, Design Systems, Prototyping'),
            ('dev.marcus@taskwave.io', 'Marcus', 'Chen', 'Employee', 'Engineering', 'EMP-005', '+1 555-100-005', 'Python, PostgreSQL, Redis, Docker'),
            ('qa.priya@taskwave.io', 'Priya', 'Sharma', 'Employee', 'Quality Assurance', 'EMP-006', '+1 555-100-006', 'Selenium, Cypress, Performance Testing, Jest'),
            ('mark.lisa@taskwave.io', 'Lisa', 'Vance', 'Employee', 'Marketing & Sales', 'EMP-007', '+1 555-100-007', 'SEO, Content Strategy, Analytics'),
            ('viewer.tom@taskwave.io', 'Tom', 'Hansen', 'Viewer', 'Product Management', 'EMP-008', '+1 555-100-008', 'Auditing, Reporting'),
        ]

        users = {}
        for email, first, last, role_name, dept_name, emp_id, phone, skills in users_seed:
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create(
                    email=email,
                    first_name=first,
                    last_name=last,
                    role=roles[role_name],
                    department=departments[dept_name],
                    employee_id=emp_id,
                    phone=phone,
                    skills=skills,
                    account_status='active',
                    is_active=True,
                    is_staff=(role_name == 'Administrator'),
                    is_superuser=(role_name == 'Administrator'),
                    joined_date=timezone.now().date() - timedelta(days=random.randint(60, 365))
                )
                user.set_password(default_pwd)
                user.save()
            users[email] = user

        # Set Department heads
        departments['Engineering'].head = users['admin@taskwave.io']
        departments['Engineering'].save()
        departments['Product Management'].head = users['pm.sarah@taskwave.io']
        departments['Product Management'].save()

        # 5. Task Categories
        cat_data = [
            ('Frontend Development', '#3b82f6', 'bi-window-stack'),
            ('Backend API', '#10b981', 'bi-server'),
            ('UI/UX Design', '#8b5cf6', 'bi-palette'),
            ('Bug Fix', '#ef4444', 'bi-bug'),
            ('DevOps & Infrastructure', '#f59e0b', 'bi-cloud'),
            ('QA & Testing', '#06b6d4', 'bi-shield-check'),
        ]
        categories = {}
        for cname, color, icon in cat_data:
            cat, _ = TaskCategory.objects.get_or_create(
                name=cname,
                defaults={'color': color, 'icon': icon}
            )
            categories[cname] = cat

        # 6. Projects
        admin_user = users['admin@taskwave.io']
        pm_user = users['pm.sarah@taskwave.io']

        projects_data = [
            {
                'name': 'Cloud Platform 2.0 Modernization',
                'description': 'Overhaul the microservices architecture, implement distributed caching with Redis, and modernize internal APIs.',
                'department': departments['Engineering'],
                'manager': pm_user,
                'status': 'active',
                'priority': 'critical',
                'category': 'web_application',
                'project_key': 'TW-CP2',
                'color': '#b45309',
                'start_date': timezone.now().date() - timedelta(days=20),
                'end_date': timezone.now().date() + timedelta(days=45),
            },
            {
                'name': 'Design System & Component Library',
                'description': 'Create comprehensive Figma tokens, dark/light theme palettes, and reusable Bootstrap components.',
                'department': departments['UI/UX Design'],
                'manager': users['lead.david@taskwave.io'],
                'status': 'active',
                'priority': 'high',
                'category': 'design',
                'project_key': 'TW-DSN',
                'color': '#8b5cf6',
                'start_date': timezone.now().date() - timedelta(days=15),
                'end_date': timezone.now().date() + timedelta(days=30),
            },
            {
                'name': 'Mobile Companion Application',
                'description': 'Cross-platform mobile client for iOS and Android providing real-time notifications and quick task updates.',
                'department': departments['Engineering'],
                'manager': pm_user,
                'status': 'planning',
                'priority': 'medium',
                'category': 'mobile_app',
                'project_key': 'TW-MOB',
                'color': '#3b82f6',
                'start_date': timezone.now().date() + timedelta(days=5),
                'end_date': timezone.now().date() + timedelta(days=90),
            },
            {
                'name': 'Automated QA & Security Pipeline',
                'description': 'Implement End-to-End Cypress integration tests and daily vulnerability scanning for SOC2 compliance.',
                'department': departments['Quality Assurance'],
                'manager': users['qa.priya@taskwave.io'],
                'status': 'active',
                'priority': 'high',
                'category': 'api',
                'project_key': 'TW-SEC',
                'color': '#10b981',
                'start_date': timezone.now().date() - timedelta(days=10),
                'end_date': timezone.now().date() + timedelta(days=25),
            },
        ]

        projects = {}
        for pdata in projects_data:
            p, _ = Project.objects.get_or_create(
                project_key=pdata['project_key'],
                defaults={**pdata, 'created_by': admin_user}
            )
            # Add members
            for u in users.values():
                ProjectMember.objects.get_or_create(project=p, user=u, defaults={'role': 'member'})
            projects[p.project_key] = p

        # Project Milestones
        milestones = [
            (projects['TW-CP2'], 'Architecture Blueprint Sign-off', timezone.now().date() - timedelta(days=5), True),
            (projects['TW-CP2'], 'Core API Endpoints Live', timezone.now().date() + timedelta(days=15), False),
            (projects['TW-CP2'], 'Load Testing & Staging Deploy', timezone.now().date() + timedelta(days=35), False),
            (projects['TW-DSN'], 'Color Palette & Typography Freeze', timezone.now().date() - timedelta(days=8), True),
            (projects['TW-DSN'], 'Bootstrap 5 Component Release v1', timezone.now().date() + timedelta(days=14), False),
        ]
        for proj, title, due, comp in milestones:
            ProjectMilestone.objects.get_or_create(project=proj, title=title, defaults={'due_date': due, 'is_completed': comp})

        # 7. Tasks
        tasks_data = [
            {
                'title': 'Design Authentication Flow & Password Reset Screens',
                'description': 'Create pixel-perfect responsive layouts matching TaskWave brand guide with amber accents and dark navigation.',
                'project': projects['TW-DSN'],
                'department': departments['UI/UX Design'],
                'category': categories['UI/UX Design'],
                'status': 'completed',
                'priority': 'high',
                'progress': 100,
                'due_date': timezone.now().date() - timedelta(days=2),
                'assignee': users['design.elena@taskwave.io'],
            },
            {
                'title': 'Implement WebSocket Consumer for Real-time Notifications',
                'description': 'Set up Django Channels ProtocolTypeRouter, channel layers on Memurai/Redis, and client auto-reconnect.',
                'project': projects['TW-CP2'],
                'department': departments['Engineering'],
                'category': categories['Backend API'],
                'status': 'in_progress',
                'priority': 'critical',
                'progress': 65,
                'due_date': timezone.now().date() + timedelta(days=3),
                'assignee': users['dev.marcus@taskwave.io'],
            },
            {
                'title': 'Build Drag-and-Drop Kanban Board with Status Transitions',
                'description': 'Ensure columns sync smoothly with database status updates via async REST API and CSRF protection.',
                'project': projects['TW-CP2'],
                'department': departments['Engineering'],
                'category': categories['Frontend Development'],
                'status': 'in_progress',
                'priority': 'high',
                'progress': 50,
                'due_date': timezone.now().date() + timedelta(days=5),
                'assignee': users['lead.david@taskwave.io'],
            },
            {
                'title': 'Audit Log Filtering and CSV Export Functionality',
                'description': 'Allow system administrators to search and export user activity logs filtered by IP, module, and timestamp.',
                'project': projects['TW-CP2'],
                'department': departments['Engineering'],
                'category': categories['Backend API'],
                'status': 'submitted',
                'priority': 'medium',
                'progress': 90,
                'due_date': timezone.now().date() + timedelta(days=1),
                'assignee': users['dev.marcus@taskwave.io'],
            },
            {
                'title': 'End-to-End Automated Testing for Task Review Workflow',
                'description': 'Cover edge cases: changes requested re-submission, file attachment validation, and reviewer approval.',
                'project': projects['TW-SEC'],
                'department': departments['Quality Assurance'],
                'category': categories['QA & Testing'],
                'status': 'assigned',
                'priority': 'high',
                'progress': 15,
                'due_date': timezone.now().date() + timedelta(days=7),
                'assignee': users['qa.priya@taskwave.io'],
            },
            {
                'title': 'Overtime Request Calculation Logic & Notification Triggers',
                'description': 'Implement rate multipliers, department manager approval gates, and automated notification dispatches.',
                'project': projects['TW-CP2'],
                'department': departments['Engineering'],
                'category': categories['Backend API'],
                'status': 'changes_requested',
                'priority': 'medium',
                'progress': 75,
                'due_date': timezone.now().date() + timedelta(days=4),
                'assignee': users['lead.david@taskwave.io'],
            },
        ]

        for tdata in tasks_data:
            assignee = tdata.pop('assignee')
            task, created = Task.objects.get_or_create(
                title=tdata['title'],
                defaults={**tdata, 'created_by': admin_user}
            )
            TaskAssignee.objects.get_or_create(task=task, user=assignee, defaults={'is_primary': True, 'assigned_by': admin_user})

            # Subtasks
            Subtask.objects.get_or_create(task=task, title='Analyze requirements & wireframes', defaults={'is_completed': True, 'order': 1})
            Subtask.objects.get_or_create(task=task, title='Core implementation & unit tests', defaults={'is_completed': (task.status == 'completed'), 'order': 2})
            Subtask.objects.get_or_create(task=task, title='Code review & documentation', defaults={'is_completed': False, 'order': 3})

            # Comments
            TaskComment.objects.get_or_create(
                task=task,
                user=admin_user,
                defaults={'content': 'Great progress! Please make sure to test responsiveness on tablet viewports.'}
            )

        # 8. Overtime Requests
        OvertimeRequest.objects.get_or_create(
            employee=users['dev.marcus@taskwave.io'],
            project=projects['TW-CP2'],
            department=departments['Engineering'],
            start_date=timezone.now().date() - timedelta(days=3),
            end_date=timezone.now().date() - timedelta(days=3),
            defaults={
                'requested_hours': 4.0,
                'approved_hours': 4.0,
                'hourly_rate': 45.0,
                'status': 'approved',
                'description': 'Critical infrastructure migration during scheduled maintenance window.',
                'reviewed_by': admin_user,
                'reviewed_at': timezone.now() - timedelta(days=2)
            }
        )

        OvertimeRequest.objects.get_or_create(
            employee=users['lead.david@taskwave.io'],
            project=projects['TW-CP2'],
            department=departments['Engineering'],
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            defaults={
                'requested_hours': 3.5,
                'status': 'pending',
                'description': 'Deploying hotfix for websocket broadcast listener.'
            }
        )

        # 9. Calendar Events
        CalendarEvent.objects.get_or_create(
            title='Engineering Daily Standup',
            defaults={
                'event_type': 'meeting',
                'start_datetime': timezone.now().replace(hour=10, minute=0, second=0),
                'end_datetime': timezone.now().replace(hour=10, minute=30, second=0),
                'location': 'Meeting Room 2 / Video Conf',
                'created_by': pm_user,
            }
        )
        CalendarEvent.objects.get_or_create(
            title='Sprint 14 Review & Retrospective',
            defaults={
                'event_type': 'review',
                'start_datetime': timezone.now() + timedelta(days=4, hours=3),
                'end_datetime': timezone.now() + timedelta(days=4, hours=4),
                'location': 'Main Conference Hall',
                'created_by': pm_user,
            }
        )

        # 10. Notifications
        for u in users.values():
            Notification.objects.get_or_create(
                recipient=u,
                title='Welcome to TaskWave!',
                defaults={
                    'notification_type': 'system',
                    'message': 'Welcome to TaskWave! You are logged in with full access to projects, tasks, and collaboration tools.',
                    'is_read': False,
                    'actor': admin_user
                }
            )

        # 11. Initial Audit Activity Log
        ActivityLog.objects.get_or_create(
            action='created',
            module='System',
            object_repr='Seed Data Generation',
            defaults={
                'user': admin_user,
                'details': 'System initialized with demo departments, users, projects, and tasks.',
                'status': 'success'
            }
        )

        self.stdout.write(self.style.SUCCESS('\n============================================================'))
        self.stdout.write(self.style.SUCCESS(' TaskWave Database Successfully Seeded!'))
        self.stdout.write(self.style.SUCCESS('============================================================'))
        self.stdout.write(f'  Admin User:      admin@taskwave.io  |  Password: {default_pwd}')
        self.stdout.write(f'  Project Manager: pm.sarah@taskwave.io|  Password: {default_pwd}')
        self.stdout.write(f'  Team Lead:       lead.david@taskwave.io| Password: {default_pwd}')
        self.stdout.write(f'  Employee:        dev.marcus@taskwave.io| Password: {default_pwd}')
        self.stdout.write(self.style.SUCCESS('============================================================\n'))
