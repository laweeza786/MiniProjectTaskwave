from django.urls import path
from apps.departments import views

app_name = 'departments'

urlpatterns = [
    path('', views.department_list_view, name='department_list'),
    path('create/', views.department_create_view, name='department_create'),
    path('<int:pk>/', views.department_detail_view, name='department_detail'),
    path('<int:pk>/edit/', views.department_edit_view, name='department_edit'),
]
