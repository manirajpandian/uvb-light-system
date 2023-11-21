# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.urls import path
from .views import login_view, register_user, new_add_user, change_password, admin_list
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('new_add_user', new_add_user, name="add_user"),
    path('admin_list', admin_list, name='user_list'),
    path('change_password/<str:token>/', change_password, name="change_password")
]
