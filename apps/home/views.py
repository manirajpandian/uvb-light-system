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
from django.db import IntegrityError
import csv
from django.db import transaction
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist


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
            total_admin = User.objects.filter(profile__role_id=2,profile__mapped_under=current_user_id).count()
      
            farm_count = Farm.objects.filter(user__id=current_user_id,is_active=True).count()
   
            house_count = House.objects.filter(farm__user_id=current_user_id,is_active=True).count()
       
            led_on_count = LED.objects.filter(pole__line__house__farm__user_id=current_user_id,is_on=True,pole__line__house__is_active=True).count()
            led_full_count = LED.objects.filter(pole__line__house__farm__user_id=current_user_id,pole__line__house__is_active=True).count()
        #Super Admin login
        elif user_role_id =='0': 
            admin_count = User.objects.filter(profile__role_id=1,is_active=True,profile__mapped_under=current_user_id).count()
            total_admin = User.objects.filter(profile__role_id=1,profile__mapped_under=current_user_id).count()
            farm_count = Farm.objects.filter(is_active=True).count()
            plant_count = Plant.objects.all().count()
      
            house_count = House.objects.filter(is_active=True).count()
     
            led_on_count = LED.objects.filter(is_on=True,pole__line__house__is_active=True).count()
            led_full_count = LED.objects.filter(pole__line__house__is_active=True).count()

        elif user_role_id =='2' :
      
            house_count = House.objects.filter(user=current_user_id,is_active=True).count()
     
            led_on_count = LED.objects.filter(pole__line__house__user=current_user_id,is_on=True,pole__line__house__is_active=True).count()
            led_full_count = LED.objects.filter(pole__line__house__user=current_user_id,pole__line__house__is_active=True).count()      
        # Assuming you want to retrieve this data for all Raspberry Pi instances
        raspberries = Rasp.objects.all()

        dashboard_sensor_data = {
            'temperature': None,
            'humidity': None,
            'soil_moisture': None,
            'raspberry_id': None,
            'date': None
        }

        # Assuming you want data for the first Raspberry instance, you can use first()
        first_raspberry = raspberries.first()

        if first_raspberry:
            # Fetch data for the first Raspberry instance
            first_data_entry = data.objects.filter(raspberry_id=first_raspberry).order_by('date').first()
           

            if first_data_entry:
                # Extract relevant information
                temperature = first_data_entry.temperature
                humidity = first_data_entry.humidity
                soil_moisture = first_data_entry.soil_moisture

                # Store the information in the dictionary
                dashboard_sensor_data = {
                    'temperature': temperature,
                    'humidity': humidity,
                    'soil_moisture': soil_moisture,
                    'raspberry_id': first_raspberry.rbi,  # Include the raspberry_id in the result
                    'date': first_data_entry.date
                }
        else:
            # Handle the case where no Raspberry instances are available
            dashboard_sensor_data = {
                'temperature': None,
                'humidity': None,
                'soil_moisture': None,
                'raspberry_id': None,
                'date': None
            }
 

        #Users Filter
        users_list = User.objects.filter(profile__role_id='1',is_active = True)
        for user in users_list:
            try:
                user.company = Company.objects.get(user=user)
            except ObjectDoesNotExist:
                user.company = None 
       
        user_id = request.GET.get('user')
        selected_user_name = None
        selected_farm_name = None
        #Farm Filter and House Display
        farms = []
        if user_role_id == '1':
            farms = Farm.objects.filter(user_id=request.user.id)
        elif user_role_id == '2':
            profile = get_object_or_404(Profile, user=request.user.id)
            farms = Farm.objects.filter(user_id = profile.mapped_under)
        else:
            if user_id:
                farms = Farm.objects.filter(user_id=user_id,is_active = True)
                selected_user_name = Company.objects.get(user_id=user_id).company_name
            else:
                farms = []

        if len(farms) > 0:
            if user_role_id == '2':
                houses = House.objects.filter(user=current_user_id,is_active=True).select_related('plant')
                farms = None
                selected_farm_name = None
                for house in houses:
                    house.house_led_on_count = LED.objects.filter(pole__line__house_id=house.house_id, is_on=True).count()
            else:
                selected_farm_id = request.GET.get('farm_id') or farm_id
                if selected_farm_id:
                    houses = House.objects.filter(farm_id=selected_farm_id,is_active=True).select_related('plant')
                    selected_farm = Farm.objects.get(pk=selected_farm_id)
                    selected_farm_name = selected_farm.farm_name  
                else:
                    if user_role_id == '0':
                        houses = []
                        for farm in farms:
                            house = House.objects.filter(farm_id=farm.farm_id,is_active=True).select_related('plant')
                            houses.extend(house)
                    else:
                        houses = []
                        for farm in farms:
                            house = House.objects.filter(is_active=True,farm_id=farm.farm_id).select_related('plant')
                            houses.extend(house)
            
                for house in houses:
                    house.house_led_on_count = LED.objects.filter(pole__line__house_id=house.house_id, is_on=True).count()
            
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
                'temperature': dashboard_sensor_data['temperature'],
                'humidity': dashboard_sensor_data['humidity'],
                'soil_moisture': dashboard_sensor_data['soil_moisture'],
                'rbi':dashboard_sensor_data['raspberry_id'],
                'led_full_count':led_full_count,   
                'plant_count':plant_count,
                 'selected_user_name':selected_user_name,   
                 'user_id':user_id,
                 'display_message': 'ハウスがありません'
                }
            if request.method == "GET":
                html_template = loader.get_template('home/dashboard.html')
                return HttpResponse(html_template.render(context, request))
            return redirect('')
    
        else:
            houses = []
            context = {'segment': 'dashboard',
                'segment': 'dashboard',
                'user_profile_image': user_profile_image,
                'user_role_id':user_role_id,
                'user_company':user_company,
                'admin_count': admin_count,
                'users_list':users_list,
                'farms': farms,
                'farm_count':farm_count,
                'house_count':house_count,
                'led_on_count':led_on_count,
                'temperature': dashboard_sensor_data['temperature'],
                'humidity': dashboard_sensor_data['humidity'],
                'soil_moisture': dashboard_sensor_data['soil_moisture'],
                'rbi':dashboard_sensor_data['raspberry_id'],
                'led_full_count':led_full_count,   
                'plant_count' : plant_count,
                'display_message': '農家を選んで下さい'
              }
            html_template = loader.get_template('home/dashboard.html')
            return HttpResponse(html_template.render(context, request))
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

@login_required(login_url="/login/")
def house_lights(request):
    context = {'segment': 'house_lights'}
    html_template = loader.get_template('home/house-lights.html')
    return HttpResponse(html_template.render(context, request))


# MQTT---Crdentials 

broker_address = "52.192.209.112"  # Replace with your local broker address
port = 1883
topic_rpi_to_ec2 = "rpi_to_ec2_topic"
topic_ec2_to_rpi = "ec2_to_rpi_topic"

mqtt_username = "dht"
mqtt_password = "dht123"


# LED Control - Sensor and LED Access
sensor_data = {
    'temperature': None,
    'humidity': None,
    'soil_moisture': None,
    'raspberry_id': None,
    'date':None,
    'led_count':4
}

latest_stored_date ={}
current_date = date.today()


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
            sensor_data , latest_stored_date , payload
    
            payload = json.loads(message.payload.decode())
            print(f"Received message from MQTT: {payload}")

            # Extract data from payload and save to the database
            sensor_data['temperature'] = payload.get('temperature')
            sensor_data['humidity'] = payload.get('humidity')
            sensor_data['soil_moisture'] = payload.get('soil_moisture')
            sensor_data['raspberry_id'] = payload.get('raspberry_id')
            sensor_data['date'] = payload.get('date')
            payload_date_str = sensor_data['date']
            
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

       
        # MQTT client for receiving sensor data
        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(username=mqtt_username, password=mqtt_password)
        mqtt_client.on_message = on_message

        # Connect to the MQTT broker
        mqtt_client.connect(broker_address, port, 60)

        # Subscribe to the topic where the Raspberry Pi publishes sensor data
        mqtt_client.subscribe(topic_rpi_to_ec2)

        # Start the MQTT loop in the background
        mqtt_client.loop_start()


        users_list = User.objects.filter(profile__role_id='1',is_active = True)
        for user in users_list:
            user.company = Company.objects.get(user=user)
        user_id = request.GET.get('user') 
        selected_farm_name = None
        selected_user_name = None
        farms = []
        if user_role_id == '1':
            farms = Farm.objects.filter(user_id=request.user.id)
        elif user_role_id == '2':
            profile = get_object_or_404(Profile, user=request.user.id)
            farms = Farm.objects.filter(user_id = profile.mapped_under)
        else:
            if user_id:
                farms = Farm.objects.filter(user_id = user_id,is_active = True)
                selected_user_name = Company.objects.get(user_id=user_id).company_name
            else:
                farms = []
            
        if len(farms) > 0:
            selected_farm_id = request.GET.get('farm_id') or farm_id
            house_id = request.GET.get('house')
            
            if house_id:
                houses = House.objects.filter(is_active=True,house_id=house_id).select_related('plant')
                selected_farm = Farm.objects.get(pk=selected_farm_id)
                selected_farm_name = selected_farm.farm_name
            else:    
                if user_role_id == '2':
                    houses = House.objects.filter(user=request.user.id,is_active=True).select_related('plant')
                    farms = []
                    
                elif user_role_id == '1':
                    
                    if selected_farm_id:
                        houses = House.objects.filter(farm_id=selected_farm_id,is_active=True,farm__user_id=request.user.id).select_related('plant')
                        selected_farm = Farm.objects.get(pk=selected_farm_id)
                        selected_farm_name = selected_farm.farm_name 
                    else:
                        houses = []
                        for farm in farms:
                            house = House.objects.filter(is_active=True,farm_id=farm.farm_id).select_related('plant')
                            houses.extend(house)       
                else:
                    if selected_farm_id:
                        houses = House.objects.filter(farm_id=selected_farm_id,is_active=True).select_related('plant')
                        selected_farm = Farm.objects.get(pk=selected_farm_id)
                        selected_farm_name = selected_farm.farm_name 
                    else:
                        houses = []
                        for farm in farms:
                            house = House.objects.filter(is_active=True,farm_id=farm.farm_id).select_related('plant')
                            houses.extend(house)
          
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
                'display_message': 'ハウスがありません',
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

                if led_id:
                    led = LED.objects.get(pk=led_id)
                    if led.is_on:  
                        led.is_on = False  # Set to False
                        led.led_off_date = timezone.now() 
                       
                        led.save()
                        print('button no',led.button_no)
                        button_data = led.button_no
                        Relay_data= False
                        if button_data > sensor_data['led_count']:
                            led_success_msg = f"Raspberry Piはその{led.led_id}に接続されていません。"         #Led is set to OFF
                            messages.error(request, led_success_msg)
                            led.led_on_date = None
                            led.is_on = False  
                            led.save()
                           
                        else:
                            # Publish button_no data to the topic
                            publish.single(topic_ec2_to_rpi, json.dumps({"button_no": button_data, "status": Relay_data}), hostname=broker_address, port=port, auth={'username': mqtt_username, 'password': mqtt_password})
                            led_success_msg = f"{led.led_id} LEDがOFFされました。"       #Led is set to OFF
                            messages.success(request, led_success_msg)
            
                    else:
                        led.is_on = True  # Set to True
                        led.led_on_date = timezone.now() 
                        
                        led.save()
                        button_data = led.button_no
                        Relay_data = True 
                        
                        if button_data > sensor_data['led_count']:
                            led_success_msg = f"Raspberry Piはその{led.led_id}に接続されていません。"       #Led is set to OFF
                            messages.error(request, led_success_msg)
                            led.led_on_date = None
                            led.is_on = False  
                            led.save()
                           
                        else:  
                        # Publish button_no data to the topic
                            publish.single(topic_ec2_to_rpi, json.dumps({"button_no": button_data, "status": Relay_data}), hostname=broker_address, port=port, auth={'username': mqtt_username, 'password': mqtt_password})
                            
                            print('button no',led.button_no)
                            led_success_msg = f"{led.led_id} LEDがONされました。"       #LED is set to ON
                            messages.success(request, led_success_msg)
               
                return redirect('LED_control_farm_id', farm_id=farm_id)
    
            return redirect('LED_control')
        else:
            context = {
                'segment': 'LED_control',
                'user_profile_image': user_profile_image,
                'user_role_id':user_role_id,
                'user_company':user_company,
                'display_message': '農家を選んで下さい',
                'users_list':users_list
                }
            return render(request,'home/LED-control.html', context)
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
        page = Paginator(plant_list, 5)
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
        selected_farm_name = None
        selected_farm_id = request.GET.get('farm_id') or farm_id
        users_list = User.objects.filter(profile__role_id='1',is_active = True)
        for user in users_list:
            user.company = Company.objects.get(user=user)
        user_id = request.GET.get('user')
        selected_user_name = None
        farms = []
        if user_role_id == '1':
            farms = Farm.objects.filter(user_id=request.user.id)
            
        elif user_role_id == '0':
            if user_id:
                farms = Farm.objects.filter(user_id = user_id,is_active = True)
                selected_user_name = Company.objects.get(user_id=user_id).company_name
            else:
                farms = Farm.objects.filter(is_active = True)             

        if len(farms) > 0:
            if selected_farm_id:
                houses = House.objects.filter(farm_id=selected_farm_id).select_related('plant')
                selected_farm = Farm.objects.get(pk=selected_farm_id)
                selected_farm_name = selected_farm.farm_name  
            else:
                if user_role_id == '0':
                    houses = []
                    for farm in farms:
                        house = House.objects.filter(farm_id=farm.farm_id).select_related('plant')
                        houses.extend(house)
                elif user_role_id == '1':
                    houses = []
                    for farm in farms:
                        house = House.objects.filter(farm_id=farm.farm_id).select_related('plant')
                        houses.extend(house)

            page = Paginator(houses, 5)
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
                            publish.single(topic_ec2_to_rpi,json.dumps({"button_no": button_no, "status": False}),hostname=broker_address,port=port,auth={'username': mqtt_username, 'password': mqtt_password})
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
                    user_id = request.GET.get('user')
                    return redirect(f'/house_list_with_farm?user={user_id}', farm_id=selected_farm_id)
                elif user_role_id == '1':
                    return redirect('house_list_with_farm', farm_id=selected_farm_id)
                else:
                    return redirect('house_list')

            return redirect('house_list')
        else:
            context = {
                'user_profile_image': user_profile_image,
                'user_role_id':user_role_id,
                'user_company':user_company,
                }
            return render(request,'home/house-list.html',context)
        
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
        user_id = request.POST.get("farmerId")
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
            is_active=True

        )
        if user_id:
            user = User.objects.get(pk=user_id)
            house.user = user
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
                    
        house_success_msg ="ハウスが正常に追加されました。"        #House is added Successfully
        messages.success(request, house_success_msg)  
        return redirect('house_list_with_farm', farm_id=farm_id)

# update house 
@login_required(login_url="/login/")
def update_house(request, house_id):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    user_company = request.session.get('user_company')
    context = {}

    try:
        house_obj = House.objects.filter(house_id=house_id).first()
        
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
            'house_obj': house_obj
        }

        if request.method == "POST":
            user_id = request.POST['user_id']
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
            
            house_obj.user_id = user_id
            house_obj.plant_id = plant_id
            house_obj.house_name = house_name
            house_obj.save()

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
            users_list = User.objects.filter(profile__role_id='1', is_active=True)
            for user in users_list:
                user.company = Company.objects.get(user=user)
            user_id = request.GET.get('user')
            selected_user_name = None
            if user_role_id == '1':
                farm_list = Farm.objects.filter(user_id = request.user.id).order_by('farm_id')
            elif user_role_id == '0':
                if user_id:
                    farm_list = Farm.objects.filter(user_id = user_id,is_active=True)
                    selected_user_name = Company.objects.get(user_id=user_id).company_name
                else:
                    farm_list = Farm.objects.filter(is_active=True)
                    
            page_number = request.GET.get('page', 1)
            paginator = Paginator(farm_list, 5)
            page = paginator.get_page(page_number)
            context = {
                'segment': 'farm_list',
                'farm_list': farm_list,
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

                        print(f"Button No: {button_no}")
                        # Publish data to MQTT
                        
                        publish.single(topic_ec2_to_rpi,json.dumps({"button_no": button_no,"status": False,}),hostname=broker_address,port=port,auth={'username': mqtt_username, 'password': mqtt_password})
                     
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

                   

                    print(f"Button No: {button_no}")

                    # Publish data to MQTT
                    publish.single(topic_ec2_to_rpi,json.dumps( {"button_no": button_no,"status":False}),hostname=broker_address,port=port,auth={'username': mqtt_username, 'password': mqtt_password})
                                      
                
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

# download
@login_required(login_url='/login/')
def LED_data_download(request):
    try:
        sensor = data.objects.all()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sensors_data.csv"'
        csv_writer = csv.writer(response)
        csv_writer.writerow(['rasp-id', 'date', 'temperature', 'humidity' , 'soil-moisture'])

        for sdata in sensor :
            csv_writer.writerow([sdata.raspberry_id ,sdata.date , sdata.temperature, sdata.humidity, sdata.soil_moisture])
            print(csv_writer)
        return response

    except BrokenPipeError as e:
        print('Download api error>>',e)
        pass
    return HttpResponse("Error occurred during CSV download.")




def RPI_settings(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    context = {'user_profile_image': user_profile_image,
            'user_role_id': user_role_id,}
    return render(request, 'home/RPI_settings.html',context)
    
def raspberryid(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    if request.method == 'POST':
        # Get the manual ID from the form data
        manual_id = request.POST.get('manual_id', '')
        request.session['manual_raspberry_id'] = manual_id
        broker_address = 'localhost'
        port = 1883
        topic = "sensor_data_topic"
        id_topic = "id_topic"
        
        
        def on_connect(client, userdata, flags, rc):
            print("Connected with result code " + str(rc))
            client.subscribe(topic)
            client.subscribe(id_topic)

        def on_message(client, userdata, msg):
            received_data = msg.payload.decode()
            
            if msg.topic == id_topic:
                # Handle ID message
                received_id = received_data.split(",")[0].strip()
                print(f"Received ID from publisher: {received_id}")
                client.publish(topic, f"ID: {received_id}")
                print(f"ID Sent to publisher: {received_id}")
            elif msg.topic == topic:
                # for mqtt data handling 
                pass

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(broker_address, port, 60)
        client.loop_start()
        client.publish(id_topic, manual_id)
        print(f"Manually Assigned ID Published: {manual_id}")
        # Set a status message to display on the RPI_settings page
        status_message = f"Manually Assigned ID Published: {manual_id}"
        context = {'user_profile_image': user_profile_image,
            'user_role_id': user_role_id,
            'status': status_message}
        
        # Render the RPI_settings page with the status message
        return render(request, 'home/RPI_settings.html', context)

    return render(request, 'home/RPI_settings.html')
        
        
        
    