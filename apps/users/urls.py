from django.urls import path
from apps.users import views

app_name = 'users'

urlpatterns = [
    path('', views.member_list_view, name='member_list'),
    path('create/', views.member_create_view, name='member_create'),
    path('profile/', views.profile_view, name='profile'),
    path('roles/', views.roles_list_view, name='roles_list'),
    path('roles/create/', views.role_create_view, name='role_create'),
    path('roles/<int:pk>/update-permissions/', views.role_update_permissions_view, name='role_update_permissions'),
    path('roles/<int:pk>/toggle-status/', views.role_toggle_status_view, name='role_toggle_status'),
    path('<int:pk>/', views.member_detail_view, name='member_detail'),
    path('<int:pk>/edit/', views.member_edit_view, name='member_edit'),
    path('<int:pk>/toggle-status/', views.member_toggle_status_view, name='member_toggle_status'),
]
