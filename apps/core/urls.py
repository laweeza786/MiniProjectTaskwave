from django.urls import path
from apps.core import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('empty-states/', views.empty_states_view, name='empty_states'),
    path('search/', views.global_search_view, name='search'),
    path('help/', views.help_support_view, name='help_support'),
]
