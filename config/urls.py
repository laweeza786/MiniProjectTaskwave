"""
TaskWave - Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Auth (login, logout, password reset, account activation)
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

    # Dashboard
    path('', include('apps.core.urls', namespace='core')),

    # Main modules
    path('projects/', include('apps.projects.urls', namespace='projects')),
    path('tasks/', include('apps.tasks.urls', namespace='tasks')),
    path('members/', include('apps.users.urls', namespace='users')),
    path('departments/', include('apps.departments.urls', namespace='departments')),
    path('kanban/', include('apps.tasks.kanban_urls', namespace='kanban')),
    path('calendar/', include('apps.calendar_app.urls', namespace='calendar_app')),
    path('messages/', include('apps.messaging.urls', namespace='messaging')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('overtime/', include('apps.overtime.urls', namespace='overtime')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('meetings/', include('apps.meetings.urls', namespace='meetings')),
    path('files/', include('apps.files.urls', namespace='files')),
    path('audit/', include('apps.audit.urls', namespace='audit')),

    # API endpoints
    path('api/', include('apps.core.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'apps.core.views.error_404'
handler403 = 'apps.core.views.error_403'
handler500 = 'apps.core.views.error_500'
