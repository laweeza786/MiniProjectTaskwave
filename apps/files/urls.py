from django.urls import path
from apps.files import views

app_name = 'files'

urlpatterns = [
    path('', views.file_list_view, name='list'),
    path('upload/', views.file_upload_view, name='upload'),
    path('<int:pk>/delete/', views.file_delete_view, name='delete'),
]
