# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Role(models.Model):
    role_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    forget_password_token = models.CharField(max_length=100)
    role_id = models.CharField(max_length=100)
    mapped_under = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_created=True, default=timezone.now)

    def __str__(self):
        return self.user.username
