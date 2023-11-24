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
    path('house_list',views.house_list, name="house_list"),
    path('add_house',views.add_house,name="add_house"),
    path('farm_manage',views.farm_manage, name="farm_manage"),
    #  path('reset_password',views.reset_password, name="reset_password"),
    path('house_lights',views.house_lights, name='house_lights'),
    path('LED_control',views.LED_control, name='LED_control'),
    path('plant_setting',views.plant_setting, name='plant_setting'),
    path('add_plant',views.add_plant, name='add_plant'),
    path('update_plant/<str:pk>',views.update_plant,name='update_plant'),
    path('delete_plant/<int:plant_id>/', views.delete_plant, name='delete_plant'),
   
    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),

]
