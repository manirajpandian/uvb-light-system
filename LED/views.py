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
def sensor_view(request):
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

    return render(request, 'home/sensor.html', context)

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
    return render(request, 'home/sensor.html', context)

