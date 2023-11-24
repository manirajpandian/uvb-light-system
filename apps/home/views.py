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

#LED Control - Sensor and LED Access
def LED_control(request,farm_id=None):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        farms = Farm.objects.all()
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
            'user_role_id':user_role_id
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
                    led.save()
                    led_success_msg = f"{led.led_id} LEDは無効化されました。"       #Led is set to OFF
                    messages.success(request, led_success_msg)
        
                else:
                    led.is_on = True  # Set to True
                    led.save()
                    led_success_msg = f"{led.led_id} LEDが活性化されました。"       #LED is set to ON
                    messages.success(request, led_success_msg)

            return redirect('LED_control_farm_id', farm_id=farm_id)

        return redirect('LED_control')
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
        lane_count = int(request.POST.get("laneCount"))
        pole_counts = [int(count) for count in request.POST.get("laneCountPerPole").split(",")]
        led_counts = [int(count) for count in request.POST.get("ledCountPerpole").split(",")]

        print("------------",user_id,house_name,plant_id,farm_id,memo,lane_count, pole_counts,led_counts)
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
    context={}
    html_template = loader.get_template('home/farm_manage.html')
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