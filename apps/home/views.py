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
from .models import Plant, Farm, House, Line, Pole, LED
from django.core.paginator import Paginator
from django.contrib import messages
from apps.authentication.models import Profile
from django.contrib.auth.models import User

from .models import Raspberrypi
import paho.mqtt.client as mqtt
import json
from django.utils import timezone
import paho.mqtt.publish as publish

from datetime import date
from django.db import IntegrityError



broker_address = "localhost"  # Replace with your local broker address
port = 1883
topic_rpi_to_ec2 = "rpi_to_ec2_topic"
topic_ec2_to_rpi = "ec2_to_rpi_topic"



@login_required(login_url="/login/")
def index(request,farm_id=None):
    try:
        print('request.user.id',request.user.id)
        current_user_id = request.user.id
        session_profile_obj, created = Profile.objects.get_or_create(user_id=current_user_id)

        user_profile_image = request.session.get('user_profile_image')
        request.session['role_id'] = session_profile_obj.role_id
        user_role_id = request.session.get('role_id')

        # Admin login active user count
        user_count = User.objects.filter(profile__role_id=2,is_active=True,profile__mapped_under=current_user_id).count()

        #Super Admin login active admin count
        admin_count = User.objects.filter(profile__role_id=1,is_active=True,profile__mapped_under=current_user_id).count()

        #Farm count under the current admin ID
        farm_count = Farm.objects.filter(user__id=current_user_id).count()

        #Active House count under the current admin ID
        house_count = House.objects.filter(farm__user_id=current_user_id,is_active=True).count()

        #Active and Inactive LED count under the current admin ID
        led_on_count = LED.objects.filter(pole__line__house__farm__user_id=current_user_id,is_on=True).count()
        led_full_count = LED.objects.filter(pole__line__house__farm__user_id=current_user_id).count()

        #Admin - Farm Filter and House Display
        farms = Farm.objects.all()
        if len(farms) > 0:
            selected_farm_id = request.GET.get('farm_id') or farm_id
            if selected_farm_id:
                houses = House.objects.filter(farm_id=selected_farm_id).select_related('plant')
                selected_farm = Farm.objects.get(pk=selected_farm_id)
                selected_farm_name = selected_farm.farm_name  
            else:
                default_farm = Farm.objects.first()
                houses = House.objects.filter(farm=default_farm).select_related('plant')
                selected_farm = default_farm
                selected_farm_name = selected_farm.farm_name
        
            for house in houses:
                house.house_led_on_count = LED.objects.filter(pole__line__house_id=house.house_id, is_on=True).count()

            #User House Display
            user_houses= House.objects.filter(user__id=current_user_id).select_related('plant')
            for house in user_houses:
                house.uHouse_led_on_count = LED.objects.filter(pole__line__house_id=house.house_id, is_on=True).count()
        
            context = {
                'segment': 'dashboard',
                'user_profile_image': user_profile_image,
                'user_role_id':user_role_id,
                'user_count': user_count,
                'admin_count': admin_count,
                'farm_count':farm_count,
                'house_count':house_count,
                'led_on_count':led_on_count,
                'led_full_count':led_full_count,
                'farms': farms,
                'houses': houses,
                'selected_farm_name': selected_farm_name,
                'user_houses':user_houses
                }
            if request.method == "GET":
                html_template = loader.get_template('home/dashboard.html')
                return HttpResponse(html_template.render(context, request))
            return redirect('')
    
        else:
            context = {'segment': 'dashboard',
               'user_profile_image': user_profile_image,
               'user_role_id':user_role_id,
               'user_count': user_count,
               'admin_count': admin_count,
               'farm_count':farm_count,
               'house_count':house_count,
               'led_on_count':led_on_count,
               'led_full_count':led_full_count,
               }
            html_template = loader.get_template('home/dashboard.html')
            return HttpResponse(html_template.render(context, request))
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

def house_lights(request):
    context = {'segment': 'house_lights'}
    html_template = loader.get_template('home/house-lights.html')
    return HttpResponse(html_template.render(context, request))


#LED Control - Sensor and LED Access
sensor_data = {
    'temperature': None,
    'humidity': None,
    'soil_moisture': None,
    'raspberry_id': None,
    'led_count': None,
    'date':None,
    'time': None,
    'address':None
}

latest_stored_date ={}
current_date = date.today()

#LED Control - Sensor and LED Access
def LED_control(request,farm_id=None):
    try:
        global sensor_data , latest_stored_date

        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        farms = Farm.objects.all()
    
        def on_message(client, userdata, message):
            sensor_data , latest_stored_date
    
            payload = json.loads(message.payload.decode())
            print(f"Received message from MQTT: {payload}")

            # Extract data from payload and save to the database
            sensor_data['temperature'] = payload.get('temperature')
            sensor_data['humidity'] = payload.get('humidity')
            sensor_data['soil_moisture'] = payload.get('soil_moisture')
            sensor_data['raspberry_id'] = payload.get('raspberry_id')
            sensor_data['date'] = payload.get('date')
            sensor_data['time'] = payload.get('timestamp')  # Assuming the timestamp is used for time
           
            raspberry_id = sensor_data['raspberry_id']
            if raspberry_id not in latest_stored_date:
                latest_stored_date[raspberry_id] = None

            raspberry_id = sensor_data['raspberry_id']

            # Check if it's a new date
            if sensor_data['date'] is not None:
                # Get the latest record for the current day and Raspberry Pi ID
                latest_record = Raspberrypi.objects.filter(
                    raspberry_id=raspberry_id,
                    # date=sensor_data['date']
                     date=current_date
                    
                ).order_by('-time').first()
                
            

                if latest_record:
                    # Update the latest record with the new data
                    latest_record.temperature = sensor_data['temperature']
                    latest_record.humidity = sensor_data['humidity']
                    latest_record.soil_moisture = sensor_data['soil_moisture']
                    latest_record.led_count = sensor_data['led_count']
                    latest_record.time = sensor_data['time']
                    latest_record.address = sensor_data['address']
                    latest_record.save()
                    print("Sensor data updated in the database:", latest_record)
                else:
                    # Save data to the database
                    sensor_db_data = Raspberrypi.objects.create(
                        temperature=sensor_data['temperature'],
                        humidity=sensor_data['humidity'],
                        soil_moisture=sensor_data['soil_moisture'],
                        raspberry_id=raspberry_id,
                        date=sensor_data['date'],
                        time=sensor_data['time'],
                  
                    )

                    print("Sensor data saved to the database:", sensor_db_data)
                       # Update the latest stored date for the current Raspberry Pi ID
                    latest_stored_date[raspberry_id] = sensor_data['date']
            else:
                print("Invalid date provided in sensor data.")

                               

            
        # MQTT client for receiving sensor data
        mqtt_client = mqtt.Client()
        mqtt_client.on_message = on_message

        # Connect to the MQTT broker
        mqtt_client.connect(broker_address, port, 60)

        # Subscribe to the topic where the Raspberry Pi publishes sensor data
        mqtt_client.subscribe(topic_rpi_to_ec2)

        # Start the MQTT loop in the background
        mqtt_client.loop_start()
        
        if len(farms) > 0:
            selected_farm_id = request.GET.get('farm_id') or farm_id
            if selected_farm_id:
                houses = House.objects.filter(farm_id=selected_farm_id).select_related('plant')
                selected_farm = Farm.objects.get(pk=selected_farm_id)
                selected_farm_name = selected_farm.farm_name  
            else:
                default_farm = Farm.objects.first()
                houses = House.objects.filter(farm=default_farm).select_related('plant')
                selected_farm = default_farm
                selected_farm_name = selected_farm.farm_name
            context = {
                'segment': 'LED_control',
                'farms': farms,
                'houses': houses,
                'selected_farm_name': selected_farm_name,
                'user_profile_image': user_profile_image,
                'user_role_id':user_role_id,
                'temperature': sensor_data['temperature'],
                'humidity': sensor_data['humidity'],
                'soil_moisture': sensor_data['soil_moisture'],
                'Rbi': sensor_data['raspberry_id'],
              
                
                }
            if request.method == "GET":
                html_template = loader.get_template('home/LED-control.html')
                return HttpResponse(html_template.render(context, request))
        
            elif request.method == "POST":
                led_id = request.POST.get('led_id')
                farm_id = request.POST.get('farm_id')

                if led_id:
                    led = LED.objects.get(pk=led_id)
                    
                    if led.is_on:  
                        led.is_on = False  # Set to False
                        led.led_off_history = timezone.now() 
                        led.save()
                        print('button no',led.button_no)
                        button_data = led.button_no
                        # Publish button_no data to the topic
                        publish.single(topic_ec2_to_rpi, json.dumps({"button_no": button_data}),
                               hostname=broker_address, port=port)

                        led_success_msg = f"{led.led_id} LEDは無効化されました。"       #Led is set to OFF
                        messages.success(request, led_success_msg)
            
                    else:
                        led.is_on = True  # Set to True
                        led.led_on_history = timezone.now() 
                        led.save()
                        button_data = led.button_no
                        # Publish button_no data to the topic
                        publish.single(topic_ec2_to_rpi, json.dumps({"button_no": button_data}),
                               hostname=broker_address, port=port)
                        print('button no',led.button_no)
                        led_success_msg = f"{led.led_id} LEDが活性化されました。"       #LED is set to ON
                        messages.success(request, led_success_msg)

                return redirect('LED_control_farm_id', farm_id=farm_id)

            return redirect('LED_control')
        else:
            context = {
                'segment': 'LED_control',
                'user_profile_image': user_profile_image,
                'user_role_id':user_role_id
                }
            return render(request,'home/LED-control.html', context)
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()


#List of plant (settings.html)
def plant_setting(request):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        plant_list = Plant.objects.all().order_by('plant_id')
        page = Paginator(plant_list, 5)
        page_list = request.GET.get('page')
        page = page.get_page(page_list)
        context = {'segment':'plant_settings', 'plant_list': plant_list,'page': page,'user_profile_image': user_profile_image,'user_role_id':user_role_id}
        if request.method == "GET":
            html_template = loader.get_template('home/settings.html')
            return HttpResponse(html_template.render(context, request))
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

    # Edit option (Updating the plant details)
def update_plant(request,pk):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        show = 'true'
        plant = Plant.objects.get(plant_id=pk)
        if request.method == 'POST':
            form = PlantForm(request.POST, instance=plant)
            if form.is_valid():
                form.save()
                plant_success_msg = '作物詳細の更新成功しました。'  #Successfully updated of crop details
                messages.success(request, plant_success_msg)
                return redirect('/plant_setting')
        else:
            form = PlantForm(instance=plant)
        context = {"form": form, "show": show, 'user_profile_image': user_profile_image,'user_role_id':user_role_id}
        return render(request, 'home/add-plant.html', context)
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))

# House list 
def house_list(request, farm_id=None):
    
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        farms = Farm.objects.all()
        if len(farms) > 0:
            selected_farm_id = request.GET.get('farm_id') or farm_id
            if selected_farm_id:
                houses = House.objects.filter(farm_id=selected_farm_id).select_related('plant')
                selected_farm = Farm.objects.get(pk=selected_farm_id)
                selected_farm_name = selected_farm.farm_name  
            else:
                default_farm = Farm.objects.first()
                houses = House.objects.filter(farm=default_farm).select_related('plant')
                selected_farm = default_farm
                selected_farm_name = selected_farm.farm_name
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
                'user_role_id':user_role_id
                }
            if request.method == "GET":
                html_template = loader.get_template('home/house-list.html')
                return HttpResponse(html_template.render(context, request))

            elif request.method == "POST":
                house_id = request.POST.get('house_id')
                farm_id = request.POST.get('farm_id')

                if house_id and farm_id:
                    house = House.objects.get(pk=house_id, farm_id=farm_id)

                    if house.is_active:  
                        house.is_active = False  # Set to False
                        house.save()

                        LED.objects.filter(pole__line__house_id=house.house_id).update(is_on=False)
                        house_success_msg = f"{house.house_name} ハウスは無効化されました。"        #House Status is set to OFF
                        messages.success(request, house_success_msg)
            
                    else:
                        house.is_active = True  # Set to True
                        house.save()
                        house_success_msg = f"{house.house_name} ハウスが活性化されました。"        #House Status is set to ON
                        messages.success(request, house_success_msg)            

                return redirect('house_list_with_farm', farm_id=farm_id)

            return redirect('house_list')
        else:
            context = {
                'user_profile_image': user_profile_image,
                'user_role_id':user_role_id
                }
            return render(request,'home/house-list.html',context)
        
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

def add_house(request):
    choice_plant = Plant.objects.all()
    choice_farm = Farm.objects.all()
    if request.user.is_authenticated:
        current_user_id = request.user.id
        mapped_profiles = Profile.objects.filter(mapped_under=current_user_id)
        
    choice_user = [profile.user for profile in mapped_profiles]
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    context = {'segment':'add_house', 
            'choice_plant': choice_plant, 
            'choice_farm': choice_farm, 
            'choice_user': choice_user, 
            'user_profile_image': user_profile_image,
            'user_role_id':user_role_id}
    if request.method == "GET":
        html_template = loader.get_template('home/add-house.html')
        return HttpResponse(html_template.render(context, request))
    else:
        user_id = request.POST.get("farmerName")
        house_name = request.POST.get("houseNameReg")
        plant_id = request.POST.get("plantNameReg")
        farm_id = request.POST.get("farmNameReg")
        memo = request.POST.get("memoReg")
        lane_count = int(request.POST.get("laneCount"))
        pole_counts = [int(count) for count in request.POST.get("laneCountPerPole").split(",")]
        led_counts = [int(count) for count in request.POST.get("ledCountPerpole").split(",")]

        house = House(
            house_name=house_name,
            memo=memo,
            total_line_count=lane_count,  
            total_pole_count=sum(pole_counts),  
            total_leds=sum(led_counts),  
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

        return redirect('/house_list')

def  farm_manage (request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    context={'user_profile_image': user_profile_image,
            'user_role_id':user_role_id
            }
    html_template = loader.get_template('home/farm_manage.html')
    return HttpResponse(html_template.render(context, request))

def  add_farm (request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    context={'user_profile_image': user_profile_image,
            'user_role_id':user_role_id
            }
    html_template = loader.get_template('home/add-farm.html')
    return HttpResponse(html_template.render(context, request))

# Add New Plant 

def add_plant(request):
    try: 
        if request.method == "GET":
            user_profile_image = request.session.get('user_profile_image')
            user_role_id = request.session.get('role_id')
            form = PlantForm()
            return render(request, 'home/add-plant.html', {"form": form,'user_profile_image': user_profile_image,'user_role_id':user_role_id})
        else:
            form = PlantForm(request.POST)
            if form.is_valid():
                form.save()
                plant_success_msg = '新しい植物の詳細が追加されました'  #New plant details has been added
                messages.success(request, plant_success_msg)
                return redirect('/plant_setting')  
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

# Delete the existing plant details
def delete_plant(request, plant_id):
    try: 
        if request.method == 'POST':
            if plant_id:
                plant = get_object_or_404(Plant, pk=plant_id)
                for house in plant.house_set.all():
                    house.is_active = False
                    house.save()
                plant.delete()
                plant_success_msg = '作物が正常に削除されました。'     #Crop successfully deleted
                messages.success(request, plant_success_msg)
                return redirect('/plant_setting')
            else:
                plant_success_msg = '作物が提供されていないです。'     #Crop was not in the list.
                messages.success(request, plant_success_msg)
                return redirect('/plant_setting')
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()
    
def delete_house(request, house_id, farm_id):
    try:
        if request.method == 'POST':
            if house_id:
                house = get_object_or_404(House, pk=house_id)
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

