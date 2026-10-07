from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import secrets

from apps.users.models import User, PasswordReset, AccountActivation
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


def forgot_password_view(request):
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
