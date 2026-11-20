from django.urls import path
from apps.audit import views

app_name = 'audit'

urlpatterns = [
    path('', views.audit_log_list_view, name='logs'),
    path('logs/', views.audit_log_list_view, name='audit_logs'),
    path('export/', views.export_audit_logs_view, name='export_logs'),
    path('settings/', views.system_settings_view, name='settings'),
    path('settings/backup/create/', views.create_backup_view, name='create_backup'),
    path('settings/backup/download/', views.download_backup_view, name='download_backup'),
    path('settings/cache/clear/', views.clear_cache_view, name='clear_cache'),
    path('settings/db/optimize/', views.optimize_db_view, name='optimize_db'),
]
