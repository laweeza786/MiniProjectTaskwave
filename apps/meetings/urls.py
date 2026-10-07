from django.urls import path
from apps.meetings import views

app_name = 'meetings'

urlpatterns = [
    path('', views.meeting_list_view, name='list'),
    path('create/', views.meeting_create_view, name='create'),
    path('room/<str:meeting_id>/', views.meeting_room_view, name='room'),
]
