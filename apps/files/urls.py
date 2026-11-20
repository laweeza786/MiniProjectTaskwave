from django.urls import path
from apps.files import views

app_name = 'files'

urlpatterns = [
    path('', views.file_list_view, name='list'),
    path('upload/', views.file_upload_view, name='upload'),
    path('create-folder/', views.folder_create_view, name='create_folder'),
    path('<int:pk>/download/', views.file_download_view, name='download'),
    path('<int:pk>/delete/', views.file_delete_view, name='delete'),
    path('<int:pk>/restore/', views.file_restore_view, name='restore'),
    path('<int:pk>/rename/', views.file_rename_view, name='rename'),
    path('<int:pk>/share/', views.file_share_view, name='share'),
]
