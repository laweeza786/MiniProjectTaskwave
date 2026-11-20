from django.urls import path
from apps.notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('<int:notification_id>/mark-read/', views.mark_notification_read_view, name='mark_read'),
    path('<int:notification_id>/delete/', views.delete_notification_view, name='delete'),
    path('bulk-action/', views.bulk_action_view, name='bulk_action'),
    path('toggle-preference/', views.toggle_preference_api, name='toggle_preference'),
    path('preferences/', views.notification_preferences_view, name='preferences'),
]
