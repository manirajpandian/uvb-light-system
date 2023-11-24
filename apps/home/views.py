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
    print('request.user.id',request.user.id)
    current_user_id = request.user.id
    session_profile_obj, created = Profile.objects.get_or_create(user_id=current_user_id)

    user_profile_image = request.session.get('user_profile_image')
    request.session['role_id'] = session_profile_obj.role_id
    user_role_id = request.session.get('role_id')

    context = {'segment': 'dashboard',
               'user_profile_image': user_profile_image,
               'user_role_id':user_role_id
               }
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
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    context={'user_profile_image': user_profile_image,
            'user_role_id':user_role_id
            }
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