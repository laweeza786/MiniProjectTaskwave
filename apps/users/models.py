"""
TaskWave Custom User Model
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('account_status', 'active')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ACCOUNT_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Activation'),
        ('suspended', 'Suspended'),
    ]

    # Basic info
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    # Skills as comma-separated or JSON
    skills = models.TextField(blank=True, help_text='Comma-separated skills')

    # Organization
    department = models.ForeignKey(
        'departments.Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='members'
    )
    role = models.ForeignKey(
        'users.Role', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users'
    )
    joined_date = models.DateField(null=True, blank=True)

    # Status
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS, default='pending')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        ordering = ['first_name', 'last_name']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        return self.first_name

    def get_initials(self):
        initials = ''
        if self.first_name:
            initials += self.first_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        return initials or 'U'

    def has_permission(self, permission_codename):
        if self.is_superuser:
            return True
        if self.role:
            return self.role.permissions.filter(codename=permission_codename).exists()
        return False

    @property
    def is_admin_user(self):
        return self.is_superuser or (self.role and self.role.name == 'Administrator')

    @property
    def profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return None


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField('users.Permission', blank=True, related_name='roles')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        ordering = ['name']

    def __str__(self):
        return self.name

    def permission_count(self):
        return self.permissions.count()


class Permission(models.Model):
    name = models.CharField(max_length=200)
    codename = models.CharField(max_length=100, unique=True)
    module = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'permissions'
        ordering = ['module', 'name']

    def __str__(self):
        return f'{self.module} - {self.name}'


class AccountActivation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activation')
    token = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'account_activations'

    def is_expired(self):
        return timezone.now() > self.expires_at


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_resets'

    def is_expired(self):
        return timezone.now() > self.expires_at
