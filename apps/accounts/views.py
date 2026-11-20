from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from datetime import timedelta
import secrets
import json
import urllib.parse
import urllib.request

from apps.users.models import User, PasswordReset, AccountActivation, Role
from apps.accounts.forms import LoginForm, ForgotPasswordForm, SetNewPasswordForm, ActivateAccountForm
from apps.audit.middleware import log_activity



def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me', False)

        user = authenticate(request, email=email, password=password)
        if user is not None:
            if user.account_status != 'active':
                messages.error(request, 'Your account is pending activation or suspended. Contact your administrator.')
                return render(request, 'accounts/login.html', {'form': form})
            
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)  # Browser close expires session
            else:
                request.session.set_expiry(86400 * 14)  # 14 days

            # Log login
            log_activity(user, 'logged_in', 'Authentication', object_repr='User login', request=request)
            
            next_url = request.GET.get('next') or 'core:dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password. Please try again.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user, 'logged_out', 'Authentication', object_repr='User logout', request=request)
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:login')


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_activity(user, 'updated', 'Security', object_repr='Password changed successfully', request=request)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:change_password')

    form = ForgotPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            expires = timezone.now() + timedelta(hours=24)
            PasswordReset.objects.create(user=user, token=token, expires_at=expires)
            # In dev, store token in session to make testing effortless
            request.session['dev_reset_token'] = token
        
        request.session['reset_email_sent_to'] = email
        return redirect('accounts:reset_link_sent')

    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_link_sent_view(request):
    email = request.session.get('reset_email_sent_to', 'your email')
    dev_token = request.session.get('dev_reset_token', None)
    return render(request, 'accounts/reset_link_sent.html', {'email': email, 'dev_token': dev_token})


def reset_password_confirm_view(request, token):
    reset_record = get_object_or_404(PasswordReset, token=token, is_used=False)
    if reset_record.is_expired():
        messages.error(request, 'This password reset link has expired. Please request a new one.')
        return redirect('accounts:forgot_password')

    form = SetNewPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_pwd = form.cleaned_data['new_password']
        user = reset_record.user
        user.set_password(new_pwd)
        user.save()

        reset_record.is_used = True
        reset_record.save()

        log_activity(user, 'changed', 'Authentication', object_repr='Password reset via token', request=request)
        return redirect('accounts:reset_successful')

    return render(request, 'accounts/reset_password.html', {'form': form, 'token': token})


def reset_successful_view(request):
    return render(request, 'accounts/reset_successful.html')


def activate_account_view(request, token):
    activation = get_object_or_404(AccountActivation, token=token, is_used=False)
    if activation.is_expired():
        messages.error(request, 'This activation link has expired. Please contact your administrator.')
        return redirect('accounts:login')

    form = ActivateAccountForm(request.POST or None, initial={
        'first_name': activation.user.first_name,
        'last_name': activation.user.last_name,
    })

    if request.method == 'POST' and form.is_valid():
        user = activation.user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.set_password(form.cleaned_data['password'])
        user.account_status = 'active'
        user.is_active = True
        user.save()

        activation.is_used = True
        activation.save()

        log_activity(user, 'activated', 'Authentication', object_repr='Account activated', request=request)
        messages.success(request, 'Your account has been activated! You can now log in.')
        return redirect('accounts:login')

    return render(request, 'accounts/activate_account.html', {'form': form, 'token': token, 'user_email': activation.user.email})


def oauth_login_view(request, provider):
    """
    Handles SSO initiation for Google and Microsoft.
    If production client credentials are configured, redirects to real OAuth provider.
    Otherwise, displays the Development SSO account picker for effortless testing.
    """
    provider = provider.lower()
    if provider not in ('google', 'microsoft'):
        messages.error(request, 'Unsupported SSO provider.')
        return redirect('accounts:login')

    google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
    microsoft_client_id = getattr(settings, 'MICROSOFT_CLIENT_ID', '').strip()

    # If real credentials exist and user didn't explicitly request dev mode
    if provider == 'google' and google_client_id and not request.GET.get('demo'):
        redirect_uri = request.build_absolute_uri(reverse('accounts:oauth_callback', args=['google']))
        params = {
            'client_id': google_client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
        }
        return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}")

    if provider == 'microsoft' and microsoft_client_id and not request.GET.get('demo'):
        tenant = getattr(settings, 'MICROSOFT_TENANT_ID', 'common') or 'common'
        redirect_uri = request.build_absolute_uri(reverse('accounts:oauth_callback', args=['microsoft']))
        params = {
            'client_id': microsoft_client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'response_mode': 'query',
        }
        return redirect(f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}")

    # Development / Demo SSO Mode
    users = User.objects.filter(is_active=True).select_related('role').order_by('id')
    
    # Preferred default demo user per provider
    if provider == 'google':
        default_user = users.filter(role__name='Administrator').first() or users.first()
        provider_name = 'Google Workspace'
        brand_color = '#4285F4'
    else:
        default_user = users.filter(role__name='Project Manager').first() or users.first()
        provider_name = 'Microsoft 365'
        brand_color = '#00a4ef'

    context = {
        'provider': provider,
        'provider_name': provider_name,
        'brand_color': brand_color,
        'users': users,
        'default_user': default_user,
    }
    return render(request, 'accounts/oauth_sso_picker.html', context)


def oauth_demo_login_view(request, provider):
    """Logs in as the selected demo user with an informative SSO badge."""
    provider = provider.lower()
    user_id = request.POST.get('user_id') or request.GET.get('user_id')

    if user_id:
        user = get_object_or_404(User, id=user_id, is_active=True)
    else:
        # Default user
        if provider == 'google':
            user = User.objects.filter(role__name='Administrator', is_active=True).first()
        else:
            user = User.objects.filter(role__name='Project Manager', is_active=True).first()
        if not user:
            user = User.objects.filter(is_active=True).first()

    if not user:
        messages.error(request, 'No active account found for demo SSO.')
        return redirect('accounts:login')

    login(request, user)
    request.session.set_expiry(86400 * 14)

    log_activity(
        user,
        'logged_in',
        'Authentication',
        object_repr=f'{provider.title()} SSO Login (Dev Mode)',
        request=request
    )

    provider_label = 'Google Workspace' if provider == 'google' else 'Microsoft 365'
    messages.success(
        request,
        f'Signed in as {user.get_full_name()} via {provider_label} (Development SSO).'
    )
    return redirect('core:dashboard')


def oauth_callback_view(request, provider):
    """Handles OAuth 2.0 callback exchange when production keys are configured."""
    provider = provider.lower()
    code = request.GET.get('code')
    error = request.GET.get('error')

    if error:
        messages.error(request, f'SSO authorization was declined: {error}')
        return redirect('accounts:login')

    if not code:
        messages.error(request, 'Missing authorization code from identity provider.')
        return redirect('accounts:login')

    try:
        if provider == 'google':
            token_url = 'https://oauth2.googleapis.com/token'
            redirect_uri = request.build_absolute_uri(reverse('accounts:oauth_callback', args=['google']))
            data = urllib.parse.urlencode({
                'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }).encode('utf-8')

            req = urllib.request.Request(token_url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_data = json.loads(resp.read().decode('utf-8'))
            
            access_token = token_data.get('access_token')
            userinfo_req = urllib.request.Request('https://www.googleapis.com/oauth2/v3/userinfo')
            userinfo_req.add_header('Authorization', f'Bearer {access_token}')
            with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
                profile = json.loads(resp.read().decode('utf-8'))

            email = profile.get('email')
            first_name = profile.get('given_name', '')
            last_name = profile.get('family_name', '')

        elif provider == 'microsoft':
            tenant = getattr(settings, 'MICROSOFT_TENANT_ID', 'common') or 'common'
            token_url = f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token'
            redirect_uri = request.build_absolute_uri(reverse('accounts:oauth_callback', args=['microsoft']))
            data = urllib.parse.urlencode({
                'code': code,
                'client_id': settings.MICROSOFT_CLIENT_ID,
                'client_secret': settings.MICROSOFT_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }).encode('utf-8')

            req = urllib.request.Request(token_url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_data = json.loads(resp.read().decode('utf-8'))

            access_token = token_data.get('access_token')
            userinfo_req = urllib.request.Request('https://graph.microsoft.com/v1.0/me')
            userinfo_req.add_header('Authorization', f'Bearer {access_token}')
            with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
                profile = json.loads(resp.read().decode('utf-8'))

            email = profile.get('mail') or profile.get('userPrincipalName')
            first_name = profile.get('givenName', '')
            last_name = profile.get('surname', '')
        else:
            messages.error(request, 'Unsupported SSO provider.')
            return redirect('accounts:login')

        if not email:
            messages.error(request, 'Could not retrieve email address from SSO profile.')
            return redirect('accounts:login')

        # Link to existing user or create a new Employee user
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            employee_role = Role.objects.filter(name='Employee').first()
            user = User.objects.create(
                email=email,
                first_name=first_name or 'SSO',
                last_name=last_name or 'User',
                role=employee_role,
                account_status='active',
                is_active=True
            )
            user.set_unusable_password()
            user.save()

        login(request, user)
        log_activity(user, 'logged_in', 'Authentication', object_repr=f'{provider.title()} SSO OAuth', request=request)
        messages.success(request, f'Welcome back, {user.first_name}!')
        return redirect('core:dashboard')

    except Exception as e:
        messages.error(request, f'SSO authentication failed: {str(e)}')
        return redirect('accounts:login')

