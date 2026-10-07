from django.urls import path
from apps.overtime import views

app_name = 'overtime'

urlpatterns = [
    path('', views.overtime_list_view, name='list'),
    path('request/', views.overtime_create_view, name='request'),
    path('<int:pk>/<str:decision>/', views.overtime_decision_view, name='decision'),
]
