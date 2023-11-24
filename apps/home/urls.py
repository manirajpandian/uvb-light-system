# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.urls import path, re_path
from apps.home import views

# from LED import Lviews

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    # path('user_list', views.user_list, name='user_list'),
    # path('add_user', views.add_user, name="add_user"),
    # path('delete_user', views.delete_user, name='delete_user'),
    # path('update_user',views.update_user,name='update_user'), #/<str:pk>
    path('house_list',views.house_list, name="house_list"),
    path('add_house',views.add_house,name="add_house"),
    path('farm_manage',views.farm_manage, name="farm_manage"),
    path('house_lights',views.house_lights, name='house_lights'),
    path('LED_control',views.LED_control, name='LED_control'),
    path('LED_control/<int:farm_id>/', views.LED_control, name='LED_control_farm_id'),
    path('plant_setting',views.plant_setting, name='plant_setting'),
    path('add_plant',views.add_plant, name='add_plant'),
    path('update_plant/<str:pk>',views.update_plant,name='update_plant'),
    path('delete_plant/<int:plant_id>/', views.delete_plant, name='delete_plant'),
  
   
    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),
    
    
    # MQTT
     path('suman', views.suman, name='suman'),
    path('toggle_led/', views.toggle_led, name='toggle_led'),
    path('update_led_status/',views. update_led_status, name='update_led_status'),
    path('publish_data/', views.publish_data, name='publish_data'),
     path('mqtt_sub/', views.mqtt_sub, name='mqtt_sub'),

]
