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
    # isActive = models.BooleanField('True')


class Employee(models.Model):
    id = models.BigAutoField(primary_key=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
