# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.db import models

# Create your models here.
class users(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    affiliation = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    houseName = models.CharField(max_length=100)
    plantName = models.CharField(max_length=100)
    isActive = models.BooleanField(default='true')
    role = models.CharField(max_length=100)
    isDeleted = models.BooleanField(default=False)
    createdBy = models.IntegerField(default=1)
    createdAt = models.DateTimeField(auto_now_add=True, blank=True)
    updatedBy = models.IntegerField(default=1)
    updatedAt = models.DateTimeField(auto_now=True, null=True)

class Role(models.Model):
    role_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)


class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=128,null=True, default='null')
    isActive = models.BooleanField(default=True, null=True)
    isDeleted = models.BooleanField(default=False, null=True)
    role_id = models.CharField(max_length=100)
    createdBy = models.IntegerField(default=1)
    createdAt = models.DateTimeField(auto_now_add=True, blank=True)
    updatedBy = models.IntegerField(default=1)
    updatedAt = models.DateTimeField(auto_now=True, null=True)

class Plant(models.Model):
    plant_id = models.BigAutoField(primary_key=True)
    plant_name = models.CharField(max_length=255)
    distance = models.DecimalField(max_digits=10, decimal_places=2)                  # Example for distance in centimeters
    time_required = models.CharField(max_length=8)                                  # Time required in minutes
    remarks = models.CharField(max_length=255)
    createdBy = models.IntegerField(default=1)
    createdAt = models.DateTimeField(auto_now_add=True, blank=True)
    updatedBy = models.IntegerField(default=1)
    updatedAt = models.DateTimeField(auto_now=True, null=True)