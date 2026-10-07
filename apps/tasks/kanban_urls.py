from django.urls import path
from apps.tasks import views

app_name = 'kanban'

urlpatterns = [
    path('', views.kanban_board_view, name='board'),
]
