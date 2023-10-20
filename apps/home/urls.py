# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('user_list', views.user_list, name='get_user_list'),
    path('add_user', views.add_user, name="add_user"),
    path('add_user',views.add_user, name="add_user"),
    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
