# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.urls import path
from .views import login_view, register_user
from django.contrib.auth.views import LogoutView
from apps.authentication import views

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('new_add_user', views.new_add_user, name="add_user"),
    path('set_password', views.set_password, name="set_password")
]
