# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.contrib import admin
from .models import users, Employee

# Register your models here.
admin.site.register(users)
admin.site.register(Employee)