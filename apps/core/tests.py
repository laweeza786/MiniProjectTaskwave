from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, Role
from apps.projects.models import Project
from apps.tasks.models import Task, Subtask
import json


class TaskWaveCoreWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role_admin = Role.objects.create(name='Administrator')
        self.admin_user = User.objects.create_superuser(
            email='testadmin@taskwave.io',
            password='TestPassword123!',
            first_name='Admin',
            last_name='User',
            role=self.role_admin,
            account_status='active'
        )

        self.project = Project.objects.create(
            name='Test Project Alpha',
            created_by=self.admin_user,
            status='active'
        )

        self.task = Task.objects.create(
            title='Test Core Deliverable',
            project=self.project,
            created_by=self.admin_user,
            status='assigned'
        )

        self.subtask = Subtask.objects.create(
            task=self.task,
            title='Write Unit Tests',
            is_completed=False
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Back')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_dashboard(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back, Admin!')

    def test_projects_list(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('projects:project_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project Alpha')

    def test_task_detail(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('tasks:task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Core Deliverable')

    def test_kanban_board(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('kanban:board'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kanban Board')

    def test_subtask_toggle_api(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            f'/api/subtasks/{self.subtask.id}/toggle/',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_completed'])

    def test_task_status_update_api(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            f'/api/tasks/{self.task.id}/update-status/',
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'in_progress')
