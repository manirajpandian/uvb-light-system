# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.db import models

# Create your models here.
class user(models.Model):
    role_id = models.CharField(max_length=100)