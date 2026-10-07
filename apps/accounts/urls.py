from django.urls import path
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-link-sent/', views.reset_link_sent_view, name='reset_link_sent'),
    path('reset-password/<str:token>/', views.reset_password_confirm_view, name='reset_password_confirm'),
    path('reset-successful/', views.reset_successful_view, name='reset_successful'),
    path('activate/<str:token>/', views.activate_account_view, name='activate_account'),
]
