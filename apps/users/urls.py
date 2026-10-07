from django.urls import path
from apps.users import views

app_name = 'users'

urlpatterns = [
    path('', views.member_list_view, name='member_list'),
    path('create/', views.member_create_view, name='member_create'),
    path('profile/', views.profile_view, name='profile'),
    path('roles/', views.roles_list_view, name='roles_list'),
    path('roles/create/', views.role_create_view, name='role_create'),
    path('<int:pk>/', views.member_detail_view, name='member_detail'),
]
