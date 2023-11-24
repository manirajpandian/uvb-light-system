
from django.urls import path, re_path
from  LED import views


from django.urls import path
from . import views





urlpatterns = [
    # The home page
    path('sensor_view/', views.sensor_view, name='sensor_view'),
    path('toggle_led/', views.toggle_led, name='toggle_led'),
    path('update_led_status/',views. update_led_status, name='update_led_status'),
    path('publish_data/', views.publish_data, name='publish_data'),
     path('mqtt_sub/', views.mqtt_sub, name='mqtt_sub'),

    
   
]
