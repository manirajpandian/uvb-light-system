# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
import json


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


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
    
@login_required(login_url="/login/")

# Initialize empty data structures

def sensor_data(request):
    temperature_data = {
            "labels": [],
            "temperatureData": [],
        }

    humidity_data = {
            "labels": [],
            "humidityData": [],
        }

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            temperature = data.get("temperature")
            humidity = data.get("humidity")

            # Process and save the data if needed
            # Update the data arrays for the graphs
            new_label = 'Label'  # Replace with appropriate data
            temperature_data['labels'].append(new_label)
            temperature_data['temperatureData'].append(temperature)
            humidity_data['labels'].append(new_label)
            humidity_data['humidityData'].append(humidity)

            # Then, you can return a JSON response indicating success.
            response_data = {
                "message": "Data received and processed successfully"
            }
            return JsonResponse(response_data)
        except Exception as e:
            response_data = {
                "error": str(e)
            }
            return JsonResponse(response_data, status=400)
    elif request.method == 'GET':
        # Serve the latest data when requested
        data = {
            "labels": temperature_data['labels'],
            "temperatureData": temperature_data['temperatureData'],
            "humidityData": humidity_data['humidityData'],
        }
        return JsonResponse(data)

    return HttpResponse("Unsupported request method", status=405)


