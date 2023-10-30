# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('user_list', views.user_list, name='user_list'),
    path('add_user', views.add_user, name="add_user"),
    path('delete_user', views.delete_user, name='delete_user'),
    path('update_user/<str:pk>',views.update_user,name='update_user'),
    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
