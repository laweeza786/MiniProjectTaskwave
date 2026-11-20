from django.urls import path
from apps.meetings import views

app_name = 'meetings'

urlpatterns = [
    path('', views.meeting_list_view, name='list'),
    path('create/', views.meeting_create_view, name='create'),
    path('instant/', views.instant_meeting_view, name='instant'),
    path('room/<str:meeting_id>/', views.meeting_room_view, name='room'),
    path('update-settings/', views.update_meeting_settings_view, name='update_settings'),
]
