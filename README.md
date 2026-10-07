# TaskWave — Enterprise Task Management & Collaboration System

TaskWave is an enterprise-grade internal task management, milestone orchestration, and team collaboration platform designed for modern organizations. Built from scratch with Python, Django, MySQL / SQLite, Django Channels, Redis/Memurai, and Bootstrap 5 with a custom warm-minimalist design system matching the approved Figma design specifications.

---

## 🚀 Key Features

- **Robust Authentication & Provisioning**:
  - Employee provisioning by Administrator (no public signups)
  - Account activation workflow with one-time verification tokens
  - Password reset via secure tokens
  - Session handling with configurable timeout policies
- **Real Role-Based Access Control (RBAC)**:
  - 5 Tiered Roles: `Administrator`, `Project Manager`, `Team Lead`, `Employee`, `Viewer`
  - Granular backend security enforcement per view and API endpoint
- **Project & Milestone Orchestration**:
  - Category and priority tagging, department allocation, manager assignments
  - Progress calculation based on completed subtasks and deliverables
  - Milestone countdowns and completion tracking
- **Task Workflow & Lifecycle**:
  - `Assigned` &rarr; `In Progress` &rarr; `Submitted for Review` &rarr; `Changes Requested` &rarr; `Completed`
  - Deliverable submission modal with notes and multi-file attachments
  - Manager review interface with decision gates (Approve, Request Changes, Reject)
  - Full audit status history tracking
- **Interactive Drag & Drop Kanban Board**:
  - Real-time column status synchronization via REST API
  - Project filtering and rapid task creation
- **Interactive Calendar & Event Scheduling**:
  - FullCalendar integration displaying task deadlines, project milestones, and meetings
- **Direct & Group Messaging**:
  - Integrated corporate chat with instant send and conversation rosters
- **Overtime Tracking & Approval**:
  - Employee overtime requests with hourly rate computations and manager sign-off
- **File Management & Document Hub**:
  - Central repository with automated file type detection, size formatting, and project linkage
- **Real-Time Video Conferences / Meetings**:
  - Video room layout with host controls, screen share controls, and participant lists
- **Audit & Security Logging**:
  - Automatic IP and user-agent logging across authentication and data mutations
- **Reporting & CSV Exports**:
  - Instant CSV exports of project status summaries and active task registries

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.11+, Django 4.2 LTS, Django REST Framework |
| **Real-Time & WebSockets** | Django Channels 4.1, ASGI (Daphne), Redis / Memurai |
| **Database** | MySQL 8.0 (Primary) / SQLite 3 (Zero-config Dev fallback) |
| **Frontend & UI** | HTML5, CSS3, Vanilla JavaScript, Bootstrap 5.3, Bootstrap Icons |
| **Charts & Calendar** | Chart.js, FullCalendar |
| **Security & Forms** | Crispy Forms (Bootstrap 5 pack), WhiteNoise |

---

## 📦 Project Directory Structure

```
TaskWave/
├── apps/
│   ├── accounts/          # Authentication, password reset, account activation
│   ├── analytics/         # Velocity charts and workload analytics
│   ├── audit/             # Activity logs, middleware, system settings
│   ├── calendar_app/      # FullCalendar feeds and event management
│   ├── core/              # Dashboard, global search, API endpoints, seed command
│   ├── departments/       # Department rosters and leadership
│   ├── files/             # Document repository and attachment management
│   ├── meetings/          # Meeting scheduling and video room UI
│   ├── messaging/         # Direct chat and conversation channels
│   ├── notifications/     # In-app alerts and preference toggles
│   ├── overtime/          # Overtime filing and manager approval
│   ├── projects/          # Project lifecycles and milestone tracking
│   ├── reports/           # Executive summaries and CSV data exports
│   ├── tasks/             # Task workflow, Kanban, comments, and reviews
│   └── users/             # Custom User model, RBAC roles & permissions
├── config/
│   ├── asgi.py            # ASGI router for HTTP & WebSockets
│   ├── settings.py        # Django configuration
│   ├── urls.py            # Global URL router
│   └── wsgi.py            # WSGI production server gateway
├── static/
│   ├── css/taskwave.css   # Custom TaskWave design system
│   └── js/taskwave.js     # Kanban drag-and-drop & AJAX interactions
├── templates/             # HTML5 templates matching Figma mockups
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
└── manage.py              # Django management CLI
```

---

## ⚡ Getting Started

### 1. Prerequisites
- Python 3.10+ installed
- Memurai or Redis running locally (default: `localhost:6379`)
- MySQL 8.0 running locally (optional; SQLite fallback enabled by default)

### 2. Setup Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the example environment file:
```powershell
Copy-Item .env.example .env
```
To use MySQL, set `DB_ENGINE=mysql`, `DB_NAME=taskwave_db`, `DB_USER=root`, and `DB_PASSWORD=your_password` in `.env`.

### 4. Database Migrations
```powershell
python manage.py migrate
```

### 5. Seed Realistic Development Data
Populates the database with departments, users, projects, tasks, comments, and milestones matching the design screenshots:
```powershell
python manage.py seed_data
```

### 6. Run Development Server
```powershell
python manage.py runserver
```
Navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## 🔑 Demo Credentials

All seed accounts use the password: `TaskWave2026!`

| Role | Email | Password | Access Scope |
|---|---|---|---|
| **Administrator** | `admin@taskwave.io` | `TaskWave2026!` | Full administrative access, audit logs, user provisioning, system settings |
| **Project Manager** | `pm.sarah@taskwave.io` | `TaskWave2026!` | Project creation, task assignment, review decisions, department overviews |
| **Team Lead** | `lead.david@taskwave.io` | `TaskWave2026!` | Task management, Kanban, review workflows, meeting scheduling |
| **Employee** | `dev.marcus@taskwave.io` | `TaskWave2026!` | Task execution, subtask checklists, work submission, overtime filing |
| **Employee (Design)** | `design.elena@taskwave.io` | `TaskWave2026!` | Design deliverables and UI review submissions |
| **Employee (QA)** | `qa.priya@taskwave.io` | `TaskWave2026!` | Automated test logs and compliance tasks |
| **Viewer** | `viewer.tom@taskwave.io` | `TaskWave2026!` | Read-only workspace inspection |

---

## 🧪 Running Automated Tests

Execute the comprehensive test suite verifying authentication, access control, Kanban API, and workflows:
```powershell
python manage.py test apps.core.tests
```
