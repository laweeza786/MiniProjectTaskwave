from django.urls import path
from apps.calendar_app import views

app_name = 'calendar_app'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('events/json/', views.calendar_events_json, name='events_json'),
    path('events/add/', views.add_calendar_event, name='add_event'),
]
