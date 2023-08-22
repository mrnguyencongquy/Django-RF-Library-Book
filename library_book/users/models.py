import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=250, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    register_date = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    created_by = models.EmailField(max_length=250)


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []