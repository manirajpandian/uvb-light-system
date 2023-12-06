# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    address = models.CharField(max_length=150,null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    forget_password_token = models.CharField(max_length=100, null=True)
    role_id = models.CharField(max_length=100, null=True)
    mapped_under = models.IntegerField(default=0,null=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    token_expiration_time = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_created=True, default=timezone.now)

    def __str__(self):
        return self.user.username


class Company(models.Model):
    company_name = models.CharField(max_length=200)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_address = models.CharField(max_length=150,null=True)
    phone = models.CharField(max_length=30,null=True)
    website = models.URLField(blank=True,null=True)
    description = models.TextField(null=True)
    created_at = models.DateTimeField(auto_created=True, default=timezone.now)

    def __str__(self):
        return self.user.username