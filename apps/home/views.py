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


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'dashboard'}
    html_template = loader.get_template('home/dashboard.html')
    return HttpResponse(html_template.render(context, request))

def house_lights(request):
    context = {'segment': 'house_lights'}
    html_template = loader.get_template('home/house-lights.html')
    return HttpResponse(html_template.render(context, request))

def LED_control(request,farm_id=None):
    choice_farm = Farm.objects.all()
    selected_farm_name = None
    if request.method == 'POST':
        farm_id = request.POST.get('selected_farm')
    else:
        farm_id = choice_farm.first().farm_id
    
    if farm_id:
            houses = House.objects.filter(farm_id=farm_id)
            selected_farm = Farm.objects.get(pk=farm_id)
            selected_farm_name = selected_farm.farm_name   
    
    context = {'segment': 'LED_control', 'choice_farm': choice_farm, 'houses': houses,'selected_farm_name': selected_farm_name, 'farm_id': farm_id}

    return render(request, 'home/LED-control.html', context)




    #List of plant (settings.html)
def plant_setting(request):
    try:
        plant_list = Plant.objects.all().order_by('plant_id')
        page = Paginator(plant_list, 5)
        page_list = request.GET.get('page')
        page = page.get_page(page_list)
        context = {'segment':'plant_settings', 'plant_list': plant_list,'page': page}
        if request.method == "GET":
            html_template = loader.get_template('home/settings.html')
            return HttpResponse(html_template.render(context, request))
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

    # Edit option (Updating the plant details)
def update_plant(request,pk):
    try:
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
        context = {"form": form, "show": show}
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

def house_list(request):
    context={}
    html_template = loader.get_template('home/house-list.html')
    return HttpResponse(html_template.render(context, request))

def add_house(request):
    choice_plant = Plant.objects.all()
    choice_farm = Farm.objects.all()
    if request.user.is_authenticated:
        current_user_id = request.user.id
        mapped_profiles = Profile.objects.filter(mapped_under=current_user_id)
        
    choice_user = [profile.user for profile in mapped_profiles]
    # print("----------->",choice_user.user.id)
    context = {'segment':'add_house', 'choice_plant': choice_plant, 'choice_farm': choice_farm, 'choice_user': choice_user}
    if request.method == "GET":
        html_template = loader.get_template('home/add-house.html')
        return HttpResponse(html_template.render(context, request))
    else:
        user_id = request.POST.get("farmerName")
        house_name = request.POST.get("houseNameReg")
        plant_id = request.POST.get("plantNameReg")
        farm_id = request.POST.get("farmNameReg")
        memo = request.POST.get("memoReg")
        # lane_count = request.POST.get("laneCount")
        # pole_count_per_lane = request.POST.get("laneCountPerPole")
        # led_count_per_pole = request.POST.get("ledCountPerpole")
        lane_count = int(request.POST.get("laneCount"))
        pole_counts = [int(count) for count in request.POST.get("laneCountPerPole").split(",")]
        led_counts = [int(count) for count in request.POST.get("ledCountPerpole").split(",")]

        print("------------",user_id,house_name,plant_id,farm_id,memo,lane_count, pole_counts,led_counts)
        house = House(
            house_name=house_name,
            memo=memo
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
    context={}
    html_template = loader.get_template('home/farm_manage.html')
    return HttpResponse(html_template.render(context, request))

# Add New Plant 

def add_plant(request):
    try: 
        if request.method == "GET":
            form = PlantForm()
            return render(request, 'home/add-plant.html', {"form": form})
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
    
    
# -------------------------------------MQTT  for Raspberry pi ----------------------------------
# Create your views here.
from django.shortcuts import render
from django.utils import timezone
import paho.mqtt.client as mqtt
import json
from datetime import date, datetime, timedelta
from .models import LineSensor
from django.http import JsonResponse , HttpResponse


# Global variable to store the latest sensor data
latest_sensor_data = {
    'temperature': 0.0,
    'humidity': 0.0,
    'soil_moisture': 0.0,
}

# Variable to store the timestamp of the last received sensor data
last_sensor_data_timestamp = None

# Timeout duration in seconds (adjust as needed)
timeout_duration = 60  # Assuming a timeout of 60 seconds
raspberry_pi_id =None

# Function to handle MQTT messages
# Function to handle MQTT messages
def on_message(client, userdata, message):
    global latest_sensor_data, last_sensor_data_timestamp, raspberry_pi_id
    try:
        payload = json.loads(message.payload.decode())
        temperature = round(payload.get("temperature"), 3)
        humidity = round(payload.get("humidity"), 3)
        soil_moisture = round(payload.get("soil_moisture"), 3)
        raspberry_pi_id = "Rpi1"

        # Reset the timestamp of the last received sensor data to indicate new data received
        last_sensor_data_timestamp = datetime.now()

        # Check if a record for the current day already exists
        today = date.today()
        existing_record = LineSensor.objects.filter(date=today).first()

        if existing_record:
            # Update the existing record for the current day
            existing_record.temperature = temperature
            existing_record.humidity = humidity
            existing_record.soil_moisture = soil_moisture
            existing_record.save()
        else:
            # Create a new record for the current day
            LineSensor.objects.create(
                date=today,
                time=timezone.now().time(),
                raspberry_pi_id=raspberry_pi_id,
                temperature=temperature,
                humidity=humidity,
                soil_moisture=soil_moisture,
            )

    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        print("Problematic payload:", message.payload.decode())
        return

    # Update the global variable with the latest sensor data
    latest_sensor_data = {
        'temperature': temperature,
        'humidity': humidity,
        'soil_moisture': soil_moisture,
    }


# MQTT broker configuration
broker_address = "localhost"  # replace with your MQTT broker address
port = 1883
topic = "rpi_to_ec2_topic"

# broker_address = "52.193.119.75"
# port = 1883
# username = "dht"
# password = "dht123"


# Set up MQTT client and subscribe to the topic
mqtt_client = mqtt.Client()
# mqtt_client.username_pw_set(username, password)
mqtt_client.on_message = on_message
mqtt_client.connect(broker_address, port, 60)
mqtt_client.subscribe(topic)
mqtt_client.loop_start()  # Start the MQTT client loop in a non-blocking way

# Django view function
def suman(request):
    print("varuthuuuuu")
    global latest_sensor_data, last_sensor_data_timestamp

    # Check if there is a timeout
    if last_sensor_data_timestamp is not None:
        time_difference = datetime.now() - last_sensor_data_timestamp
        if time_difference.total_seconds() > timeout_duration:
            # If there is a timeout, set all sensor values to zero
            latest_sensor_data = {
                'temperature': 0.0,
                'humidity': 0.0,
                'soil_moisture': 0.0,
            }

    # If latest_sensor_data is not None, use the received data; otherwise, set default values
    temperature = latest_sensor_data['temperature']
    humidity = latest_sensor_data['humidity']
    soil_moisture = latest_sensor_data['soil_moisture']

    context = {
        'temperature': temperature,
        'humidity': humidity,
        'soil_moisture': soil_moisture,
        "Rbi": raspberry_pi_id
    }
    print(context)

    return render(request, 'home/suman.html', context)

def publish_data(request):
    global mqtt_client

    # You can add more validation or security checks here if needed

    # Request data from the MQTT publisher
    request_data = {"request": "publish_data"}
    request_json = json.dumps(request_data)
    mqtt_client.publish("request_topic", payload=request_json, qos=1)

    # You can add a response message or handle the response as needed
    response_message = "Data publish request sent to the publisher."

    return JsonResponse({"message": response_message})

def toggle_led(request):
    if request.method == 'POST' and 'led_number' in request.POST:
        led_number = request.POST['led_number']
        print('LED number received:', led_number)
        # Add your logic to handle the LED number as needed

        # You can return a JsonResponse if needed
        return JsonResponse({'message': 'LED number received successfully'})

    return JsonResponse({'error': 'Invalid request'}, status=400)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def update_led_status(request):
    if request.method == 'POST':
        led_no = request.POST.get('ledNo')
        is_checked = request.POST.get('isChecked')
        print ("data", led_no, is_checked)
        
        # Perform actions based on LED status (on/off)
        # Your logic to update LED status goes here

        response_data = {'message': 'LED status updated successfully'}
        return JsonResponse(response_data)
    else:
        response_data = {'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)
   

import json
import threading
import paho.mqtt.client as mqtt
from django.http import HttpResponse
from django.shortcuts import render
from django.dispatch import Signal, receiver

# Define signals for manual input and sending relay information
manual_input_signal = Signal()
send_relay_information_signal = Signal()


broker_address = "localhost"
port = 1883

# broker_address = "52.193.119.75"
# port = 1883
# username = "dht"
# password = "dht123"

topic_rpi_to_ec2 = "rpi_to_ec2_topic"
topic_ec2_to_rpi = "ec2_to_rpi_topic"

ec2_client = mqtt.Client()

# ec2_client.username_pw_set(username, password)
relay_number_input = None
input_lock = threading.Lock()
relay_status = None
relay_status_lock = threading.Lock()

def on_message_ec2(client, userdata, message):
    global relay_status
    payload = json.loads(message.payload.decode())
    print(f"Received message from Raspberry Pi: {payload}")

    with relay_status_lock:
        relay_status = payload.get("relay_status")

ec2_client.connect(broker_address, port, 60)
ec2_client.on_message = on_message_ec2
ec2_client.subscribe(topic_rpi_to_ec2)

@receiver(manual_input_signal)
def manual_input(sender, led_no, **kwargs):
    global relay_number_input
    try:
        relay_number = int(led_no)
        with input_lock:
            if relay_number != relay_number_input:
                relay_number_input = relay_number
                with relay_status_lock:
                    relay_status = {"relay_number": relay_number}
    except ValueError:
        print("Invalid input. Please enter a valid number.")

@receiver(send_relay_information_signal)
def send_relay_information(sender, **kwargs):
    global relay_status
    with relay_status_lock:
        if relay_status is not None:
            # ec2_client.publish(topic_ec2_to_rpi, json.dumps({"relay_control": relay_status}))
            relay_status = None

def mqtt_sub(request):
    led_no = None
    if request.method == 'POST':
        led_no = request.POST.get('ledNo')
        is_checked = request.POST.get('isChecked')
        print("data >>>>>>>>>>>>>", led_no, is_checked)
        ec2_client.publish(topic_ec2_to_rpi, json.dumps({"relay_control": led_no}))
        # Trigger the manual input signal
        manual_input_signal.send(sender=None, led_no=led_no)

        # Trigger the send relay information signal
        send_relay_information_signal.send(sender=None)

    context = {}  # Use an empty dictionary as the context
    return render(request, 'home/suman.html', context)

