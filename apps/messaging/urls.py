from django.urls import path
from apps.messaging import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('start/<int:user_id>/', views.start_direct_message, name='start_direct'),
    path('create/', views.create_conversation_view, name='create_conversation'),
    path('send/<int:conversation_id>/', views.send_message_api, name='send_message'),
    path('poll/<int:conversation_id>/', views.poll_messages_api, name='poll_messages'),
    path('conversation/<int:conversation_id>/', views.conversation_detail_api, name='conversation_detail_api'),
]
