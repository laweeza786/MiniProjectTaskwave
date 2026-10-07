from django.urls import path
from apps.messaging import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('start/<int:user_id>/', views.start_direct_message, name='start_direct'),
    path('send/<int:conversation_id>/', views.send_message_api, name='send_message'),
]
