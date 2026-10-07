from django.urls import path
from apps.reports import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_overview_view, name='overview'),
    path('export/tasks/', views.export_tasks_csv, name='export_tasks'),
    path('export/projects/', views.export_projects_csv, name='export_projects'),
]
