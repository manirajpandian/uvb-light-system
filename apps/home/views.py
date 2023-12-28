# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.template import loader
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PlantForm

from django.core.paginator import Paginator
from django.contrib import messages
from apps.authentication.models import Profile,Company,Plant, Farm, House, Line, Pole, LED, data , Rasp
from django.contrib.auth.models import User
import paho.mqtt.client as mqtt
import json
from django.utils import timezone
import paho.mqtt.publish as publish
from datetime import date, datetime
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import codecs
from django.http import StreamingHttpResponse
from urllib.parse import quote
from django.db import IntegrityError
import csv
import threading



def company_filter(user_role_id, request,list=None):

    users_list = User.objects.filter(profile__role_id='1', is_active=True)
    for user in users_list:
        try:
            user.company = Company.objects.get(user=user)
        except ObjectDoesNotExist:
            user.company = None

    user_id = request.GET.get('user')
    selected_user_name = None

    if user_role_id == '1':
        farms = Farm.objects.filter(user_id=request.user.id)
    elif user_role_id == '2':
        profile = get_object_or_404(Profile, user=request.user.id)
        farms = Farm.objects.filter(user_id=profile.mapped_under)
    elif user_role_id == '0':
        if user_id:
            farms = Farm.objects.filter(user_id=user_id, is_active=True)
            selected_user_name = Company.objects.get(user_id=user_id).company_name
        elif list:
            farms = Farm.objects.filter(is_active=True)
        else:
            farms = []

    return users_list, user_id, selected_user_name, farms

def house_filter(user_role_id, farms, request, selected_farm_id,house_list=None):
    houses = []
    selected_farm_name = None
    display_message = None
    if len(farms) > 0:
        if user_role_id == '2':
            houses = House.objects.filter(user=request.user.id, is_active=True)
            farms = []
            selected_farm_name = None
        else:
            if selected_farm_id:
                houses = House.objects.filter(farm_id=selected_farm_id) if house_list else House.objects.filter(farm_id=selected_farm_id, is_active=True)
                selected_farm_name = Farm.objects.get(pk=selected_farm_id).farm_name          
            else:
                if user_role_id == '0':
                    for farm in farms:
                        house = House.objects.filter(farm_id=farm.farm_id) if house_list else House.objects.filter(farm_id=farm.farm_id, is_active=True)
                        houses.extend(house)
                else:
                    for farm in farms:
                        house = House.objects.filter(farm_id=farm.farm_id) if house_list else House.objects.filter(is_active=True, farm_id=farm.farm_id)
                        houses.extend(house)

    elif len(farms) == 0:
        display_message = '農家を選んで下さい'

    return houses,selected_farm_name,display_message

@login_required(login_url="/login/")
def index(request,farm_id=None):
    try:
        current_user_id = request.user.id
        session_profile_obj, created = Profile.objects.get_or_create(user_id=current_user_id)
        user_profile_image = request.session.get('user_profile_image')
        request.session['role_id'] = session_profile_obj.role_id
        user_role_id = request.session.get('role_id')
        if user_role_id == '0':
            user_company = 'BEAM TECH'
        elif user_role_id == '1' :
            user_company = Company.objects.get(user_id=request.user.id).company_name
        else:
            mapped_under = Profile.objects.get(pk=request.user.id).mapped_under
            user_company = Company.objects.get(user_id=mapped_under).company_name
        request.session['user_company'] = user_company
        

        plant_count = None
        admin_count = None
        farm_count = None
        # Admin login
        if user_role_id =='1':
            admin_count = User.objects.filter(profile__role_id=2,is_active=True,profile__mapped_under=current_user_id).count()
            farm_count = Farm.objects.filter(user__id=current_user_id,is_active=True).count()
            house_count = House.objects.filter(farm__user_id=current_user_id,is_active=True).count()
            led_on_count = LED.objects.filter(pole__line__house__farm__user_id=current_user_id,is_on=True,pole__line__house__is_active=True).count()
            led_full_count = LED.objects.filter(pole__line__house__farm__user_id=current_user_id,pole__line__house__is_active=True).count()

        #Super Admin login
        elif user_role_id =='0': 
            user_id = request.GET.get('user')
            if user_id:
                farm_count = Farm.objects.filter(user__id=user_id,is_active=True).count()
                house_count = House.objects.filter(farm__user__id=user_id).count()
                led_on_count = LED.objects.filter(pole__line__house__farm__user_id=user_id,is_on=True,pole__line__house__is_active=True).count()
                led_full_count = LED.objects.filter(pole__line__house__farm__user_id=user_id,pole__line__house__is_active=True).count()

            else:   
                admin_count = User.objects.filter(profile__role_id=1,is_active=True).count()
                farm_count = Farm.objects.filter(is_active=True).count()
                plant_count = Plant.objects.all().count()
                house_count = House.objects.filter(is_active=True).count()
                led_on_count = LED.objects.filter(is_on=True,pole__line__house__is_active=True).count()
                led_full_count = LED.objects.filter(pole__line__house__is_active=True).count()

        elif user_role_id =='2' :
            house_count = House.objects.filter(user=current_user_id,is_active=True).count()
            led_on_count = LED.objects.filter(pole__line__house__user=current_user_id,is_on=True,pole__line__house__is_active=True).count()
            led_full_count = LED.objects.filter(pole__line__house__user=current_user_id,pole__line__house__is_active=True).count() 


        
        
        
        display_data = None
        house_id = request.GET.get('house')
        
 

        #Company Filter
        users_list, user_id, selected_user_name, farms = company_filter(user_role_id, request)
        selected_farm_id = request.GET.get('farm_id') or farm_id
        #House Filter
        houses,selected_farm_name,display_message = house_filter(user_role_id, farms, request, selected_farm_id)

        for house in houses:
                house.house_led_on_count = LED.objects.filter(pole__line__house_id=house.house_id, is_on=True).count()
        rasp_dic ={}
        
        for house in houses:
            rasp_set = set()
            led_range = LED.objects.filter(pole__line__house__house_id=house.house_id)
            for led in led_range:
                rasp_set.add(led.rasp_id)
            rasp_dic[house.house_id] = rasp_set
    
        for house in houses:
            if house.house_id in rasp_dic.keys():
                for items in rasp_dic[house.house_id]:
                    if items != None:
                        display_data = data.objects.get(raspberry_id_id = items)
                        if display_data.temperature:
                            house.temp = display_data.temperature
                            house.hum = display_data.humidity
                            house.mos = display_data.soil_moisture
                            house.rbi = display_data.raspberry_id_id
                            print("==================", house.temp , house.temp)
                    else:
                        house.temp = None
                        house.hum = None
                        house.mos = None
                        house.rbi = None
                        print("==================", house.temp , house.temp)
            
        context = {
                'segment': 'dashboard',
                'user_profile_image': user_profile_image,
                'user_role_id':user_role_id,
                'user_company':user_company,
                'admin_count': admin_count,
                'users_list':users_list,
                'farms': farms,
                'houses': houses,
                'selected_farm_name': selected_farm_name,
                'farm_count':farm_count,
                'house_count':house_count,
                'led_on_count':led_on_count,
                'led_full_count':led_full_count,   
                'plant_count':plant_count,
                'selected_user_name':selected_user_name,   
                'user_id':user_id,
                'display_message': display_message
                }
        if request.method == "GET":
            html_template = loader.get_template('home/dashboard.html')
            return HttpResponse(html_template.render(context, request))
        return redirect('')
    
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

@login_required(login_url="/login/")
def house_lights(request):
    context = {'segment': 'house_lights'}
    html_template = loader.get_template('home/house-lights.html')
    return HttpResponse(html_template.render(context, request))


# MQTT---Crdentials 

broker_address = "localhost" 
# broker_address = "52.192.209.112"  # Replace with your local broker address
port = 1883
topic_rpi_to_ec2 = "rpi_to_ec2_topic"
topic_ec2_to_rpi = "ec2_to_rpi_topic"
data_receiving_topic = "data_receiving_topic"
relay_topic = 'relay_topic'
mqtt_username = "dht"
mqtt_password = "dht123"


# LED Control - Sensor and LED Access
sensor_data = {
    'temperature': None,
    'humidity': None,
    'soil_moisture': None,
    'raspberry_id': None,
    'date':None,
    'led_count':23,
    'message1':None
}

latest_stored_date ={}
current_date = date.today()

rasp_dic = {}
#LED Control - Sensor and LED Access
@login_required(login_url="/login/")

#LED Control - Sensor and LED Access
def LED_control(request,farm_id=None):
   
    try:
        global sensor_data , latest_stored_date
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        user_company = request.session.get('user_company')
        @transaction.atomic
        def on_message(client, userdata, message):
            sensor_data , latest_stored_date
            payload = json.loads(message.payload.decode())
            print(f"Received message from MQTT: {payload}")
            # Extract data from payload and save to the database
            ID= payload.get('raspberry_id')
            temp = payload.get('temperature')
            soil = payload.get('soil_moisture')
            matching_rasps = Rasp.objects.filter(rbi=ID)

            if matching_rasps.exists():
                
                
                if temp and soil != None :
                       
                        sensor_data['temperature'] = payload.get('temperature')
                        sensor_data['humidity'] = payload.get('humidity')
                        sensor_data['soil_moisture'] = payload.get('soil_moisture')
                        sensor_data['raspberry_id'] = payload.get('raspberry_id')
                        sensor_data['date'] = payload.get('date')
                        payload_date_str = sensor_data['date']
                        sensor_data['message1'] = payload.get('message')
                        if payload_date_str:
                            sensor_data['date'] = datetime.strptime(payload_date_str, "%Y-%m-%d %H:%M:%S").date()
                        else:
                            print("Invalid date provided in sensor data.")
                            return
                    
                        # Inside your on_message function
                        raspberry_id = sensor_data['raspberry_id']
                        rasp_instance, created = Rasp.objects.get_or_create(rbi=raspberry_id)
                        

                        if raspberry_id not in latest_stored_date:
                            latest_stored_date[raspberry_id] = None

                        # Check if it's a new date
                        if sensor_data['date'] is not None:
                            sensor_db_data, created = data.objects.update_or_create(
                            raspberry_id=rasp_instance,
                            date=sensor_data['date'],
                            defaults={
                            'temperature': sensor_data['temperature'],
                            'humidity': sensor_data['humidity'],
                            'soil_moisture': sensor_data['soil_moisture'],
                            }
                                )

                            # if created:
                            #     print("Sensor data saved to the database:", sensor_db_data)
                            # else:
                            #     print("Sensor data updated in the database:", sensor_db_data)

                                # Update the latest stored date for the current Raspberry Pi ID
                            latest_stored_date[raspberry_id] = sensor_data['date']
                            
                
                        else:
                            print("Invalid date provided in sensor data.")
                else:
             
                   print('null data is detected ') 
            else :
                print("data is not matching ")
  
        #Company Filter
        users_list, user_id, selected_user_name, farms = company_filter(user_role_id, request)

        house_id = request.GET.get('house')
        selected_farm_id = request.GET.get('farm_id') or farm_id
        if house_id:
                houses = House.objects.filter(is_active=True,house_id=house_id)
                selected_farm_name = Farm.objects.get(pk=selected_farm_id).farm_name
                display_message = None
        else:
            houses,selected_farm_name,display_message = house_filter(user_role_id, farms, request, selected_farm_id)
        
        global rasp_dic
        
        for house in houses:
            rasp_set = set()
            led_range = LED.objects.filter(pole__line__house__house_id=house.house_id)
            for led in led_range:
                rasp_set.add(led.rasp_id)
            rasp_dic[house.house_id] = rasp_set
    
        
        
        # MQTT client for receiving sensor data
        mqtt_client = mqtt.Client()
        # mqtt_client.username_pw_set(username=mqtt_username, password=mqtt_password)
        mqtt_client.on_message = on_message

        # Connect to the MQTT broker
        mqtt_client.connect(broker_address, port, 60)

        # Subscribe to the topic where the Raspberry Pi publishes sensor data
        mqtt_client.subscribe(topic_rpi_to_ec2)

        # Start the MQTT loop in the background
        mqtt_client.loop_start()

        # display_data = None
        
        # for house in houses:
        #     if house.house_id in rasp_dic.keys():
        #         for items in rasp_dic[house.house_id]:
        #             if items != None:
        #                 display_data = data.objects.get(raspberry_id_id = items)
        #                 if display_data.temperature:
        #                     house.temp = display_data.temperature
        #                     house.hum = display_data.humidity
        #                     house.mos = display_data.soil_moisture
        #                     house.rbi = display_data.raspberry_id_id
        #             else:
        #                 house.temp = None
        #                 house.hum = None
        #                 house.mos = None
        #                 house.rbi = None
        
        display_data = None
        selected_raspberry_id = None

        for house in houses:
            if house.house_id in rasp_dic.keys():
                for items in rasp_dic[house.house_id]:
                    if items is not None:
                        try:
                            display_data = data.objects.get(raspberry_id_id=items)
                            selected_raspberry_id = items
                            break  # Exit the loop once data for one Raspberry Pi is found
                        except data.DoesNotExist:
                            pass  # Handle the case where data doesn't exist for the current Raspberry Pi
                else:
                    # This block will execute if the inner loop completes without a 'break'
                    selected_raspberry_id = None

                # Update house attributes based on the selected Raspberry Pi data
                house.temp = display_data.temperature if display_data else None
                house.hum = display_data.humidity if display_data else None
                house.mos = display_data.soil_moisture if display_data else None
                house.rbi = selected_raspberry_id
            else:
                # Handle the case where the house ID is not in rasp_dic.keys()
                house.temp = None
                house.hum = None
                house.mos = None
                house.rbi = None

                            
        context = {
            'segment': 'LED_control',
            'farms': farms,
            'houses': houses,
            'selected_farm_name': selected_farm_name,
            'user_profile_image': user_profile_image,
            'user_role_id':user_role_id,
            'user_company':user_company,
            'temperature': sensor_data['temperature'],
            'humidity': sensor_data['humidity'],
            'soil_moisture': sensor_data['soil_moisture'],
            'Rbi': sensor_data['raspberry_id'],
            'users_list':users_list,
            'led_count':sensor_data['led_count'],
            'message1':sensor_data['message1'],
            'display_message': display_message,
            'selected_farm_name':selected_farm_name,
            'user_id':user_id,
            'selected_user_name':selected_user_name,
            } 
    
        if request.method == "GET":

            if context['temperature'] or context ['humidity'] or context['soil_moisture'] is None:
                context['message'] = "Raspberry pi "
                html_template = loader.get_template('home/LED-control.html')
                return HttpResponse(html_template.render(context, request))
            html_template = loader.get_template('home/LED-control.html')
            return HttpResponse(html_template.render(context, request))
            
        elif request.method == "POST":
            led_id = request.POST.get('led_id')
            farm_id = request.POST.get('farm_id')
            user_id = Farm.objects.get(pk=farm_id).user_id
            if led_id:
                led = LED.objects.get(pk=led_id)
                
                if led.is_on:  
                    led.is_on = False  # Set to False
                    led.led_off_date = timezone.now() 
                    led.save()

                    print('button no',led.button_no)
                    button_data = led.button_no
                    led_rasid = led.rasp_id
                    Relay_data= False
                    if button_data > sensor_data['led_count']:
                        led_success_msg = f"Raspberry Piはその{led.led_id}に接続されていません。"         #Led is set to OFF
                        messages.error(request, led_success_msg)
                        led.led_on_date = None
                        led.is_on = False  
                        led.save()
                    else:
                        # Publish button_no data to the topic
                        message = {'button_no': button_data, 'status': Relay_data ,  'raspberrypi_id': led_rasid }
                       
                        json_message = json.dumps(message)
                        # publish.single(topic_ec2_to_rpi, json.dumps({"button_no": button_data, "status": Relay_data}), hostname=broker_address, port=port, auth={'username': mqtt_username, 'password': mqtt_password})
                        publish.single(relay_topic, json_message, hostname=broker_address,port=port)
                        mqtt_client.publish(relay_topic, json_message)
                        print('relay data published ', message )
                        led_success_msg = f"{led.led_id} LEDがOFFされました。"       #Led is set to OFF
                        messages.success(request, led_success_msg)
                else:
                    led.is_on = True  # Set to True
                    led.led_on_date = timezone.now() 
                    led.save()

                    print('button no',led.button_no)
                    button_data = led.button_no
                    led_rasid = led.rasp_id
                    Relay_data = True 
                    if button_data > sensor_data['led_count']:
                        led_success_msg = f"Raspberry Piはその{led.led_id}に接続されていません。"       #Led is set to OFF
                        messages.error(request, led_success_msg)
                        led.led_on_date = None
                        led.is_on = False  
                        led.save()
                        
                    else:  
                    # Publish button_no data to the topic
                        message = {'button_no': button_data, 'status': Relay_data ,  'raspberrypi_id': led_rasid }
                        print(message)
                        json_message = json.dumps(message)
                       
                        # publish.single(topic_ec2_to_rpi, json.dumps({"button_no": button_data, "status": Relay_data}), hostname=broker_address, port=port, auth={'username': mqtt_username, 'password': mqtt_password})
                        publish.single(relay_topic, json_message,hostname=broker_address, port=port,)
                        mqtt_client.publish(relay_topic, json_message,)
                        print('relay data published ', message )
                        led_success_msg = f"{led.led_id} LEDがONされました。"       #LED is set to ON
                        messages.success(request, led_success_msg)
            if user_role_id == '0':
                url = reverse('LED_control_farm_id', kwargs={'farm_id': farm_id}) + f'?user={user_id}'
                return redirect(url)
            else:
                return redirect('LED_control_farm_id', farm_id=farm_id)

        return redirect('LED_control')
      
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()




#List of plant (settings.html)
@login_required(login_url="/login/")
def plant_setting(request):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        user_company = request.session.get('user_company')
        plant_list = Plant.objects.all().order_by('plant_id')
        for plant in plant_list:
            plant.active_houses_count = plant.house_set.filter(is_active=True).count()
        page = Paginator(plant_list, 10)
        page_list = request.GET.get('page')
        page = page.get_page(page_list)
        context = {'segment':'plant_settings', 'plant_list': plant_list,'page': page,'user_profile_image': user_profile_image,'user_role_id':user_role_id,'user_company':user_company,}
        if request.method == "GET":
            html_template = loader.get_template('home/settings.html')
            return HttpResponse(html_template.render(context, request))
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

    # Edit option (Updating the plant details)
@login_required(login_url="/login/")
def update_plant(request,pk):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        user_company = request.session.get('user_company')
        show = 'true'
        plant = Plant.objects.get(plant_id=pk)
        if request.method == 'POST':
            form = PlantForm(request.POST, instance=plant)
            if form.is_valid():
                form.save()
                plant_success_msg = '作物詳細の更新が成功しました'  #Successfully updated of crop details
                messages.success(request, plant_success_msg)
                return redirect('/plant_setting')
        else:
            form = PlantForm(instance=plant)
        context = {"form": form, "show": show, 'user_profile_image': user_profile_image,'user_role_id':user_role_id,'user_company':user_company,}
        return render(request, 'home/add-plant.html', context)
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()


@login_required(login_url="/login/")
def pages(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    user_company = request.session.get('user_company')
    context = {
        'user_profile_image': user_profile_image,
        'user_role_id':user_role_id,
        'user_company':user_company,
    }
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        user_company = request.session.get('user_company')
       
        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template
        print("test", context)

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))

# House list 
@login_required(login_url="/login/")
def house_list(request, farm_id=None):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        user_company = request.session.get('user_company')
        
        #Company Filter
        list = True
        house_list = True
        users_list, user_id, selected_user_name, farms = company_filter(user_role_id, request,list)   
        selected_farm_id = request.GET.get('farm_id') or farm_id      
        
        #House Filter
        houses,selected_farm_name,display_message = house_filter(user_role_id, farms, request, selected_farm_id,house_list)
     
        for house in houses:
            house.user_count = house.user.count()
            if house.user_count == 0:
                house.user_count = '管理者'
            house.ledoncount = LED.objects.filter(pole__line__house__house_id=house.house_id, is_on=True).count()
             

        page = Paginator(houses, 10)
        page_list = request.GET.get('page')
        page = page.get_page(page_list) 
        context = {
            'farms': farms,
            'houses': houses,
            'selected_farm_name': selected_farm_name,
            'page': page,
            'selected_farm_id': selected_farm_id,
            'user_profile_image': user_profile_image,
            'user_role_id':user_role_id,
            'user_company':user_company,
            'users_list':users_list,
            'user_id':user_id,
            'selected_user_name':selected_user_name,
            'farm_id':farm_id,
            }
            
        if request.method == "GET":
            html_template = loader.get_template('home/house-list.html')
            return HttpResponse(html_template.render(context, request))

        elif request.method == "POST":
            house_id = request.POST.get('house_id')
            farm_id = request.POST.get('farm_id')
            selected_farm_id = request.GET.get('farm_id') or farm_id
            user_id = Farm.objects.get(pk=farm_id).user_id
            if house_id and farm_id:
                house = House.objects.get(pk=house_id, farm_id=farm_id)

                if house.is_active:  
                    house.is_active = False  # Set to False
                    house.save()

                    leds = LED.objects.filter(pole__line__house_id=house.house_id)
                    for led in leds:
                        button_no = led.button_no
                        print(f"Button No: {button_no}")
                        # Publish data to MQTT
                        # publish.single(topic_ec2_to_rpi,json.dumps({"button_no": button_no, "status": False}),hostname=broker_address,port=port,auth={'username': mqtt_username, 'password': mqtt_password})
                        publish.single(topic_ec2_to_rpi,json.dumps({"button_no": button_no, "status": False}),hostname=broker_address,port=port,)
                        led.is_on = False
                        led.save() 
                    house_success_msg = f"{house.house_name} ハウスは無効化されました。"        #House Status is set to OFF
                    messages.success(request, house_success_msg)
        
                else:
                    house.is_active = True  # Set to True
                    house.save()
                    house_success_msg = f"{house.house_name} ハウスが活性化されました。"        #House Status is set to ON
                    messages.success(request, house_success_msg)            

            if selected_farm_id and user_role_id == '0':
                url = reverse('house_list_with_farm', kwargs={'farm_id': selected_farm_id}) + f'?user={user_id}'
                return redirect(url)
            elif user_role_id == '1':
                 return redirect('house_list_with_farm', farm_id=selected_farm_id)
            else:
                return redirect('house_list')

        return redirect('house_list')

    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

@login_required(login_url="/login/")
def add_house(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    user_company = request.session.get('user_company')
    user_id = request.GET.get('user')
    choice_plant = Plant.objects.all()
    selected_user_name = None
    if user_role_id == '0':
        choice_farm = Farm.objects.filter(user_id=user_id)
        selected_user_name = Company.objects.get(user_id=user_id).company_name
    elif user_role_id == '1':
        choice_farm = Farm.objects.filter(user_id=request.user.id)
    
    if request.user.is_authenticated:
        if user_role_id == '1':
            current_user_id = request.user.id
        elif user_role_id == '0':
            current_user_id = user_id
        mapped_profiles = Profile.objects.filter(mapped_under=current_user_id,user__is_active=True)
            
    choice_user = [profile.user for profile in mapped_profiles]
    
    context = {'segment':'add_house', 
            'choice_plant': choice_plant, 
            'choice_farm': choice_farm, 
            'choice_user': choice_user, 
            'user_profile_image': user_profile_image,
            'user_role_id':user_role_id,
            'user_company':user_company,
            'selected_user_name':selected_user_name,
            }
    if request.method == "GET":
        html_template = loader.get_template('home/add-house.html')
        return HttpResponse(html_template.render(context, request))
    else:
        user_id_get = request.POST.get("farmerId")
        user_id_list = user_id_get.split(",") if user_id_get else []
        user_id_list = [user_id for user_id in user_id_list if user_id.strip()]   
        house_name = request.POST.get("houseNameReg")
        plant_id = request.POST.get("plantIdReg")
        farm_id = request.POST.get("farmIdReg")
        memo = request.POST.get("memoReg")
        lane_count = int(request.POST.get("laneCount"))
        pole_counts = [int(count) for count in request.POST.get("arrayPolePLC").split(',')]
        led_counts = [int(count) for count in request.POST.get("arrayLED").split(',')]
        sum_pole_counts = int(request.POST.get("laneCountPerPole"))
        sum_led_counts = int(request.POST.get("ledCountPerpole"))


        house = House(
            house_name=house_name,
            memo=memo,
            total_line_count=lane_count,  
            total_pole_count=sum_pole_counts,  
            total_leds=sum_led_counts,  
            is_active=True,
        )
        
        if plant_id:
            house.plant_id = plant_id
        if farm_id:
            farm_id
            house.farm_id = farm_id
        house.save()

        for i in range(1, lane_count + 1):
            line = Line(
                house=house,
                pole_count=pole_counts[i - 1]
            )
            line.save()

            # Create Pole and LED instances
            for j in range(1, pole_counts[i - 1] + 1):
                pole = Pole(
                    line=line,
                    led_count=led_counts.pop(0)
                )
                pole.save()

                # Create LED instances
                for k in range(1, pole.led_count + 1):
                    led = LED(
                        pole=pole
                    )
                    led.save()
        
    
        for user_id in user_id_list:
            each_user = User.objects.get(pk=user_id).id
            house.user.add(each_user)
                    
        house_success_msg ="ハウスが正常に追加されました。"        #House is added Successfully
        messages.success(request, house_success_msg)
        if user_role_id == '0':
            user_id = request.GET.get('user') 
            return redirect(f'/house_list?user={user_id}')
        elif user_role_id == '1':
            return redirect('house_list_with_farm', farm_id=farm_id)

# update house 
@login_required(login_url="/login/")
def update_house(request, house_id):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    user_company = request.session.get('user_company')
    context = {}
    house_user_id = []

    try:
        house_obj = House.objects.filter(house_id=house_id).first()
        for house in house_obj.user.all():
            house_user_id.append(house.id)
        
        if request.user.is_authenticated:
            current_user_id = Farm.objects.get(houses__house_id=house_id).user.id
            mapped_profiles = Profile.objects.filter(mapped_under=current_user_id)
            choice_user = [profile.user for profile in mapped_profiles]
                
        else:
            choice_user = []

        choice_plant = Plant.objects.all()
        context = {
            'segment': 'update_house',
            'user_profile_image': user_profile_image,
            'user_role_id': user_role_id,
            'user_company': user_company,
            'choice_user': choice_user,
            'choice_plant': choice_plant,
            'house_obj': house_obj,
            'house_user_id':house_user_id
        }

        if request.method == "POST":
            user_id = request.POST['user_id'] or None
            if user_id != None:
                print('user_id',user_id,type(user_id))
                user_ids = user_id.split(',')
            else:
                user_ids = []

            plant_id = request.POST['plant_id']
            house_name = request.POST['house_name']

            if house_name == '':
                context = {
            'segment': 'update_house',
            'errorMessage': 'ハウス名は空欄であってはなりません',
            'user_profile_image': user_profile_image,
            'user_role_id': user_role_id,
            'user_company': user_company,
            'choice_user': choice_user,
            'choice_plant': choice_plant,
            'house_obj': house_obj}
                return render(request, 'home/update-house.html', context)
            
            # house_obj.user_id = user_id
            house_obj.plant_id = plant_id
            house_obj.house_name = house_name
            house_obj.save()
            house_obj.user.set(user_ids)

            message = f"ハウス{house_obj.house_name} が更新されました"
            messages.success(request, message)
            return redirect('/house_list')

    except Exception as e:
        print('+++++update_house error+++++', e)

    return render(request, 'home/update-house.html', context)


# List of farm (farm_list.html)
@login_required(login_url="/login/")
def farm_list(request):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        user_company = request.session.get('user_company')
        if request.method == "GET":
            #Company Filter
            list = True
            users_list, user_id, selected_user_name, farms = company_filter(user_role_id, request,list)   

            for farm in farms:
                farm.ledoncount = LED.objects.filter(pole__line__house__farm__farm_id=farm.farm_id, is_on=True).count()

            page_number = request.GET.get('page', 1)
            paginator = Paginator(farms, 10)
            page = paginator.get_page(page_number)
            context = {
                'segment': 'farm_list',
                'farm_list': farms,
                'page': page,
                'user_profile_image': user_profile_image,
                'user_role_id': user_role_id,
                'user_company':user_company,
                'users_list':users_list,
                'user_id':user_id,
                'selected_user_name':selected_user_name,
            }

            html_template = loader.get_template('home/farm_list.html')
            return HttpResponse(html_template.render(context, request))

        elif request.method == "POST":
            farm_id = request.POST.get('farm_id')
            farm_name = request.POST.get('farm_name')
            address = request.POST.get('address')
            farm_obj = Farm.objects.get(farm_id=farm_id)
            farm_obj.farm_name = farm_name
            farm_obj.address = address
            farm_obj.save()
            message = f"農場{farm_obj.farm_name} が更新されました"
            messages.success(request, message)
            if user_role_id == '1':
                return redirect('farm_list')
            elif user_role_id == '0':
                return redirect(f'/farm_list?user={farm_obj.user_id}')

    except BrokenPipeError as e:
        print('Exception BrokenPipeError', e)
        return HttpResponseServerError()

    return HttpResponse(status=400)



#Add New farm
@login_required(login_url="/login/")
def add_farm(request):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        user_company = request.session.get('user_company')

        if request.method == 'POST':
            farm_name = request.POST.get('farm_name')
            address = request.POST.get('address')
            if user_role_id == '0':
                user = request.POST.get('user_id') 
                url = reverse('farm_list') + f'?user={user}'
            elif user_role_id == '1':
                user = request.user.id
                url = reverse('farm_list')
            farm = Farm(farm_name=farm_name, address=address,user_id=user)
            farm.save()
            messages.success(request, '新しい農場の詳細が追加されました')
            return redirect(url)
          
        context = {
            'segment': 'farm_list',
            'user_profile_image': user_profile_image,
            'user_role_id': user_role_id,
            'user_company': user_company,
        }
        return render(request, 'home/farm_list.html', context)

    except BrokenPipeError as e:
        print('Exception BrokenPipeError', e)
        return HttpResponseServerError()
      
#Delete option (Deleting the farm details)
@login_required(login_url="/login/")
def delete_farm(request, farm_id):
    try: 
        user_role_id = request.session.get('role_id')
        if request.method == 'POST':
            if farm_id:
                farm = get_object_or_404(Farm, pk=farm_id)
                houses_to_delete = House.objects.filter(farm=farm)
                for house in houses_to_delete:
                    leds = LED.objects.filter(pole__line__house=house)
                    print(leds)
                    for led in leds :
                        button_no = led.button_no
                        led_rasid = led.rasp_id
                        print(f"Button No: {button_no}")
                        # Publish data to MQTT
                        
                        # publish.single(topic_ec2_to_rpi,json.dumps({"button_no": button_no,"status": False,}),hostname=broker_address,port=port,auth={'username': mqtt_username, 'password': mqtt_password})
                        publish.single(topic_ec2_to_rpi,json.dumps({"button_no": button_no,"status": False,  'raspberrypi_id': led_rasid}),hostname=broker_address,port=port)
                    house.delete()
                farm.delete()
                farm_success_msg = '農場が正常に削除されました。'  # Farm successfully deleted
                messages.success(request, farm_success_msg)
                if user_role_id == '1':
                    return redirect('farm_list')
                elif user_role_id == '0':
                    return redirect(f'/farm_list?user={farm.user_id}')
            else:
                farm_success_msg = '農場が提供されていないです。'  # Farm was not in the list.
                messages.success(request, farm_success_msg)
                if user_role_id == '1':
                    return redirect('farm_list')
                elif user_role_id == '0':
                    return redirect(f'/farm_list?user={farm.user_id}')
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()


# Add New Plant 
@login_required(login_url="/login/")
def add_plant(request):
    try: 
        if request.method == "GET":
            user_profile_image = request.session.get('user_profile_image')
            user_role_id = request.session.get('role_id')
            user_company = request.session.get('user_company')
            form = PlantForm()
            return render(request, 'home/add-plant.html', {"form": form,'user_profile_image': user_profile_image,'user_role_id':user_role_id,'user_company':user_company,})
        else:
            form = PlantForm(request.POST, request=request)
            if form.is_valid():

                form.save()
                plant_success_msg = '新しい作物の詳細が追加されました'  #New plant details has been added
                messages.success(request, plant_success_msg)
                return redirect('/plant_setting')  
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

# Delete the existing plant details
@login_required(login_url="/login/")
def delete_plant(request, plant_id):
    try: 
        if request.method == 'POST':
            if plant_id:
                plant = get_object_or_404(Plant, pk=plant_id)
                plant.delete()
                plant_success_msg = '作物が正常に削除されました。'     #Crop successfully deleted
                messages.success(request, plant_success_msg)
                return redirect('/plant_setting')
            else:
                plant_success_msg = '作物の削除中にエラーがありました。'     #Error in deleting the plant.
                messages.success(request, plant_success_msg)
                return redirect('/plant_setting')
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()
    
@login_required(login_url="/login/")
def delete_house(request, house_id, farm_id):
    try:
        if request.method == 'POST':
            if house_id:
                house = get_object_or_404(House, pk=house_id)
                print("----------house",house)
                # leds = LED.objects.filter(pole__line__house_house_id=house)
                leds = LED.objects.filter(pole__line__house=house)

                print('----------------------------leds',leds)
                for led in leds:
                    button_no = led.button_no
                    led_rasid = led.rasp_id

                   

                    print(f"Button No: {button_no}")

                    # Publish data to MQTT
                    # publish.single(topic_ec2_to_rpi,json.dumps( {"button_no": button_no,"status":False}),hostname=broker_address,port=port,auth={'username': mqtt_username, 'password': mqtt_password})
                    publish.single(topic_ec2_to_rpi,json.dumps( {"button_no": button_no,"status":False, 'raspberrypi_id': led_rasid}),hostname=broker_address,port=port,)
                                      
                if house_id in rasp_dic.keys():
                    rbi_items = rasp_dic[house_id]
                    Rasp.objects.filter(rbi__in=rbi_items).update(is_assigned=None)
                        
                house.delete()
                house_success_msg = f'{house.house_name}ハウスが正常に削除されました。'     # House successfully deleted
                messages.success(request, house_success_msg)  
                if farm_id:
                    return redirect('house_list_with_farm', farm_id=farm_id)
                else:
                    return redirect('house_list')

    except BrokenPipeError as e:
        print('Exception BrokenPipeError', e)
        return HttpResponseServerError()
    
# write the csv file here 
class Echo:
    def write(self, value):
        return value

# csv content generate 
def generate_csv_content(house_id):
    LEDs = LED.objects.filter(led_id__startswith=house_id)
    # Todo: different RasberryPi were used please change this query
    sensor_data = data.objects.get(raspberry_id_id='Rpi-4')

    yield codecs.BOM_UTF8 + bytes(','.join(['LED No', '温度', '湿度', '土壌', 'ON_時間', 'OFF_時間']) + '\n', 'utf-8')

    for led in LEDs:
        on_time = '' 
        off_time = ''
        if None != led.led_on_date:
            on_time = led.led_on_date.strftime("%H:%M:%S")
        if None != led.led_off_date:
            off_time = led.led_off_date.strftime("%H:%M:%S")
        row = f"{led.led_id},{sensor_data.temperature},{sensor_data.humidity},{sensor_data.soil_moisture},{on_time},{off_time}\n"
        yield bytes(row, 'utf-8')

# csv file download 
def LED_data_download(request):
    try:
        house_id = request.GET.get('house_id')
        house = House.objects.get(house_id=house_id)
        
        # file name with date 
        now = timezone.now()
        formatted_date = now.strftime("%d-%m-%Y %H:%M:%S")
        file_name = f"{quote(house.house_name)}_{formatted_date}.csv"

        response = StreamingHttpResponse(generate_csv_content(house_id), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        return response

    except BrokenPipeError as e:
        print('Download API error:', e)
        pass

    return HttpResponse("Error occurred during CSV download.")


# Set your MQTT broker information
topic = "sensor_data_topic"
id_topic = "id_topic"
relay_topic ='relay_topic'
test ='test'
# Set to store unique publisher IDs
publisher_ids = set()
publisher_ids_lock = threading.Lock()
context={}


def RPI_settings(request,farm_id=None):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    user_company = request.session.get('user_company')
    company_id = None
    filter_house = None
    house_id = None
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe(topic)
        client.subscribe(id_topic)
 

    def print_available_ids():
        # with publisher_ids_lock:
            print("Available IDs:")
            for i, publisher_id in enumerate(publisher_ids, start=1):
                print(f"{i}. {publisher_id}")
                # print('context>>>>>loop',context)

    def on_message(client, userdata, msg):
        received_data = msg.payload.decode()
        
        if not received_data:
            print("Received empty message.")
            return

        if msg.topic == topic:
         
            try:
                data = json.loads(received_data)
                relay_id = data.get("relay_id")
                if relay_id:
                    with publisher_ids_lock:
                        publisher_ids.add(relay_id)
                    print_available_ids()
                    print(f"Received data from ID {relay_id}: {received_data}")

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                
        elif msg.topic == id_topic:
            
                data = json.loads(received_data)
                RPI_id = data.get("raspberry_id")
                
                if RPI_id:
                    with publisher_ids_lock:
                        publisher_ids.add(RPI_id)
                    print_available_ids()
                
        elif request.method == 'POST':
                print ('inside of the post method ')
            # Extract data from payload and save to the database
                sensor_data['temperature'] = data.get('temperature')
                sensor_data['humidity'] = data.get('humidity')
                sensor_data['soil_moisture'] = data.get('soil_moisture')
                sensor_data['raspberry_id'] = data.get('raspberry_id')
                sensor_data['date'] = data.get('date')
                payload_date_str = sensor_data['date']
                sensor_data['message1'] = data.get('message')
                
                if payload_date_str:
                    
                    sensor_data['date'] = datetime.strptime(payload_date_str, "%Y-%m-%d %H:%M:%S").date()
                    
                else:
                    print("Invalid date provided in sensor data.")
                    return
            
                # Inside your on_message function
                raspberry_id = sensor_data['raspberry_id']
                rasp_instance, created = Rasp.objects.get_or_create(rbi=raspberry_id)
                

                if raspberry_id not in latest_stored_date:
                    latest_stored_date[raspberry_id] = None

                # Check if it's a new date
                if sensor_data['date'] is not None:
                    sensor_db_data, created = data.objects.update_or_create(
                    raspberry_id=rasp_instance,
                    date=sensor_data['date'],
                    defaults={
                    'temperature': sensor_data['temperature'],
                    'humidity': sensor_data['humidity'],
                    'soil_moisture': sensor_data['soil_moisture'],
                    }
                        )

                    if created:
                        print("Sensor data saved to the database:", sensor_db_data)
                    else:
                        print("Sensor data updated in the database:", sensor_db_data)

                        # Update the latest stored date for the current Raspberry Pi ID
                    latest_stored_date[raspberry_id] = sensor_data['date']
                    
        
                else:
                    print("Invalid date provided in sensor data.")
            
           
    client = mqtt.Client() 
    # client.username_pw_set(username=mqtt_username, password=mqtt_password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_address, port, 60)
    

    # Create threads for on_relay and on_message functions
    # thread_on_relay = threading.Thread(target=on_relay)
    thread_on_message = threading.Thread(target=client.loop_start)

    # Start the threads
    # thread_on_relay.start()
    thread_on_message.start()
    # Fetch all existing rbi values from the database
    all_rbis = Rasp.objects.all()

    paginator = Paginator(all_rbis, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    company_id = request.GET.get('company_id')
    house_id = request.GET.get('house_id')
    
    filter_farm = Farm.objects.filter(user_id=company_id)
    for farm in filter_farm:
        filter_house = House.objects.filter(farm_id=farm.farm_id)
    
    filtered_LEDs = LED.objects.filter(pole__line__house__house_id=house_id,rasp__isnull=True).order_by('led_id')
    filtered_Rpi = Rasp.objects.filter(is_assigned__isnull=True)

    group_size = 23
    filter_LED_count = []
    for i in range(0, len(filtered_LEDs), group_size):
        start_index = i
        end_index = min(i + group_size, len(filtered_LEDs))
        current_group = filtered_LEDs[start_index:end_index]
        
        button_nos = [item.button_no for item in current_group]
        first_id = current_group[0].led_id
        last_id = current_group[-1].led_id
        result = f'1-{(len(button_nos))},[{first_id} - {last_id}]'
        filter_LED_count.append(result)

    array_raspberry = list(publisher_ids)
    print ('>>>>>>>>>>>>>>>>>>>>>>>', array_raspberry)
    print('=========',house_id)
   
    choice_companies = Company.objects.filter(user__is_active=True, user__is_superuser = False)
    context = {
            'user_profile_image': user_profile_image,
            'user_role_id': user_role_id,
            'page': page,  
            'user_company': user_company,
            'rbis': all_rbis,
            'raspberry':list (publisher_ids),
            'choice_companies':choice_companies,
            'company_id':company_id,
            'selected_house_id':house_id,
            'filter_house':filter_house,
            'filtered_LEDs':filtered_LEDs,
            'filter_LED_count':filter_LED_count,
            'filtered_Rpi':filtered_Rpi,
        }
    if request.method == 'GET':
        return render(request, 'home/RPI_settings.html', context)  
    elif request.method == 'POST':

        led_selection = request.POST.get('ledAssign')
        rpi_selection = request.POST.get('rpiAssign')
        company_id = request.POST.get('companyselect')
        house_id = request.POST.get('houseselect')

        led_selection_range = [led_id for led_id in led_selection.split(',')]
        cleaned_string = led_selection_range[1].strip('[]')
        led_selection_range = cleaned_string.split(' - ')
        start_led_id, end_led_id = led_selection_range[0], led_selection_range[1]
        rasp_instance = Rasp.objects.get(rbi=rpi_selection)
        LEDs_to_update = LED.objects.filter(led_id__range=(start_led_id, end_led_id))
        for led in LEDs_to_update:
            led.rasp = rasp_instance
            led.save()

        house_name = House.objects.get(house_id=str(house_id))
        company_name = Company.objects.get(id = company_id)
        rasp_instance.is_assigned = f'{company_name.company_name} -> {house_name} -> {led_selection_range}'
        rasp_instance.save()
        context = {
            'user_profile_image': user_profile_image,
            'user_role_id': user_role_id,
            'page': page,  
            'user_company': user_company,
            'rbis': all_rbis,
            'raspberry':list (publisher_ids),
            'choice_companies':choice_companies,
            'filter_house':filter_house,
            'filtered_LEDs':filtered_LEDs,
            'filter_LED_count':filter_LED_count,
            'filtered_Rpi':filtered_Rpi,
        }
        return render(request, 'home/RPI_settings.html',context)  

def add_RPI(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    user_company = request.session.get('user_company')

    all_rbis = Rasp.objects.values_list('rbi', flat=True).order_by('rbi')

    paginator = Paginator(all_rbis, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    print('page>>>', page)
    print('')
    array_raspberry = list(publisher_ids)
    print ('>>>>>>>>>>>>>>>>>>>>>>>', array_raspberry)
   

    context = {
            'user_profile_image': user_profile_image,
            'user_role_id': user_role_id,
            'page': page,  # Pass all rbi values to the template
            'user_company': user_company,
            'rbis': all_rbis,
            'raspberry':list (publisher_ids),
        }
    
    
    if request.method == 'POST':
        rpi_id = request.POST.get('ras', None)
        print("welcome///////?????????????????", rpi_id)
        if not rpi_id:
            error_msg = "RpiID is required"
            messages.error(request, error_msg)
            return redirect('/RPI_settings')
        else:
            try:
                Rasp.objects.create(rbi=rpi_id)
                all_rbis = Rasp.objects.values_list('rbi', flat=True)
                context.update({
                    'success': True,
                    'rbis': all_rbis,
                    'user_profile_image': user_profile_image,
                    'user_role_id': user_role_id,
                    'page': page,
                    'user_company': user_company,
                 
                    'raspberry': list(publisher_ids)
                })
                messages.success(request, 'RpiID added successfully')
                print('>>>>>>>>>.befor success')
                # return render(request, 'home/RPI_settings.html', context)
                return redirect('/RPI_settings')
            except IntegrityError as e:
                print(f"Error: {e}")
                messages.error(request, 'Error adding RpiID to the database. Duplicate entry.')
                return redirect('/RPI_settings')
            except Exception as e:
                print(f"Error: {e}")
                messages.error(request, 'Error adding RpiID to the database')
                return redirect('/RPI_settings')

    return render(request, 'home/RPI_settings.html', context)




