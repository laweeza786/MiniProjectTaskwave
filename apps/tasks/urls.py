from django.urls import path
from apps.tasks import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list_view, name='task_list'),
    path('create/', views.task_create_view, name='task_create'),
    path('<int:pk>/', views.task_detail_view, name='task_detail'),
    path('<int:pk>/edit/', views.task_edit_view, name='task_edit'),
    path('<int:pk>/delete/', views.task_delete_view, name='task_delete'),
    path('<int:pk>/comments/add/', views.add_task_comment_view, name='add_comment'),
    path('<int:pk>/subtasks/add/', views.add_subtask_view, name='add_subtask'),
    path('<int:pk>/submit/', views.submit_task_view, name='submit_task'),
    path('<int:pk>/submissions/<int:submission_id>/review/', views.review_task_view, name='review_task'),
]
