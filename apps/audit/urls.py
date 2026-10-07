from django.urls import path
from apps.audit import views

app_name = 'audit'

urlpatterns = [
    path('', views.audit_log_list_view, name='logs'),
    path('settings/', views.system_settings_view, name='settings'),
]
