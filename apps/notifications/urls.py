from django.urls import path
from apps.notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('preferences/', views.notification_preferences_view, name='preferences'),
]
