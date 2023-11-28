# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('<int:farm_id>/', views.index, name='home_with_farm'),
    path('house_list',views.house_list, name="house_list"),
    path('house_list/<int:farm_id>/', views.house_list, name='house_list_with_farm'),
    path('delete_house/<str:house_id>/', views.delete_house, name='delete_house'),
    path('delete_house/<str:house_id>/<int:farm_id>/', views.delete_house, name='delete_house_with_farm'),
    path('add_house',views.add_house,name="add_house"),
    path('update_house/<str:farm_id>', views.update_house, name='update_house'),
    path('farm_manage',views.farm_manage, name="farm_manage"),
    path('house_lights',views.house_lights, name='house_lights'),
    path('LED_control',views.LED_control, name='LED_control'),
    path('LED_control/<int:farm_id>/', views.LED_control, name='LED_control_farm_id'),
    path('plant_setting',views.plant_setting, name='plant_setting'),
    path('add_plant',views.add_plant, name='add_plant'),
    path('update_plant/<str:pk>',views.update_plant,name='update_plant'),
    path('delete_plant/<int:plant_id>/', views.delete_plant, name='delete_plant'),
    path('add_farm',views.add_farm, name='add_farm'),
 
   
    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),
    


]
