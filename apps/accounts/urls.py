from django.urls import path
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-link-sent/', views.reset_link_sent_view, name='reset_link_sent'),
    path('reset-password/<str:token>/', views.reset_password_confirm_view, name='reset_password_confirm'),
    path('reset-successful/', views.reset_successful_view, name='reset_successful'),
    path('activate/<str:token>/', views.activate_account_view, name='activate_account'),
    path('oauth/<str:provider>/', views.oauth_login_view, name='oauth_login'),
    path('oauth/<str:provider>/callback/', views.oauth_callback_view, name='oauth_callback'),
    path('oauth/<str:provider>/demo-login/', views.oauth_demo_login_view, name='oauth_demo_login'),
]

