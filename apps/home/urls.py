# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views
from . import views


from .views import (
    LogIn,
    success,
    user_logout,
    SignUp
)

urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),
    path('sensor_data', views.sensor_data, name='sensor_data'),
    
    # new data 
     path("apilogin/", LogIn.as_view(), name="login"),
    path("apisuccess/", success, name="success"),
    path("apilogout/", user_logout, name="logout"),
    path("apisignup/", SignUp.as_view(), name="signup"),
     path('api/generate_permanent_token/', views.generate_permanent_token, name='generate_permanent_token'),
    path('api/receive_data/', views.receive_data, name='receive_data'),
    path("api/test/", views.test, name="suman")
    # Add other URL patterns as needed

]
