# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, JsonResponse
from django.template import loader
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserAddForm,PlantForm
from .models import User,Plant
from django.core.paginator import Paginator
import json
from django.contrib import messages


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'dashboard'}
    html_template = loader.get_template('home/dashboard.html')
    return HttpResponse(html_template.render(context, request))

def house_lights(request):
    context = {'segment': 'house_lights'}
    html_template = loader.get_template('home/house-lights.html')
    return HttpResponse(html_template.render(context, request))

def LED_control(request):
    context = {'segment' : 'LED_control'}
    html_template = loader.get_template('home/LED-control.html')
    return HttpResponse(html_template.render(context, request))

def plant_setting(request):
    try:
        plant_list = Plant.objects.all().order_by('plant_id')
        context = {'segment':'plant_settings', 'plant_list': plant_list}
        # page = Paginator(user_list, 5)
        # page_list = request.GET.get('page')
        # page = page.get_page(page_list)
        print(context)
        if request.method == "GET":
            print(plant_list)
            # return render(request, 'home/settings.html', {'plant_list': plant_list})
            html_template = loader.get_template('home/settings.html')
            return HttpResponse(html_template.render(context, request))
        # elif request.method == "POST":
        #     user_id = request.POST['user_id']
        #     is_active = request.POST['is_active']
        #     user = get_object_or_404(User, pk=user_id)
        #     user.isActive = is_active
        #     user.save()
        #     success_message = "ユーザーステータスの変更に成功しました"  # success message here
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()
    
def update_plant(request,pk):
    show = 'true'
    plant = Plant.objects.get(plant_id=pk)
    if request.method == 'POST':
        form = PlantForm(request.POST, instance=plant)
        if form.is_valid():
            form.save()
            update_success_message = '作物詳細の更新成功'
            messages.success(request, update_success_message)
            return redirect('/plant_setting')
    else:
        form = PlantForm(instance=plant)
    context = {"form": form, "show": show}
    return render(request, 'home/add-plant.html', context)

# Add new user

@login_required
def add_user(request):
    if request.method == "GET":
        form = UserAddForm()
        return render(request, 'home/add-user.html', {"form": form})
    else:
        form = UserAddForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                error_message = "このメールはすでに存在します。別のメールをお試しください。"
                return render(request, 'home/add-user.html', {'form': form, 'error_message': error_message})  # Redirect to the same page
            else:
                form.save()
                add_success_message = "ユーザが正常に追加されました"
                messages.success(request, add_success_message)
                return redirect('/user_list')
        else:
            # Handle the case when the form is not valid
            error_message = "無効なフォームデータです。フォームフィールドを確認して、もう一度やり直してください。"
            return render(request, 'home/add-user.html', {'form': form, 'error_message': error_message}) # Redirect to the same page


# Get user list and Active/Disabled user

def user_list(request):
    try:
        user_list = User.objects.filter(isDeleted=False).order_by('user_id')
        page = Paginator(user_list, 5)
        page_list = request.GET.get('page')
        page = page.get_page(page_list)
        if request.method == "GET":
            return render(request, 'home/admin.html', {'page': page})
        elif request.method == "POST":
            user_id = request.POST['user_id']
            is_active = request.POST['is_active']
            user = get_object_or_404(User, pk=user_id)
            user.isActive = is_active
            user.save()
            success_message = "ユーザーステータスの変更に成功しました"  # success message here
        return render(request, 'home/admin.html', {'page': page, 'success_message': success_message, 'page': page})
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
        return HttpResponseServerError()

 # Update User

def update_user(request, pk):
    show = 'true'
    user = User.objects.get(user_id=pk)
    if request.method == 'POST':
        form = UserAddForm(request.POST, instance=user)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exclude(user_id=pk).exists():
                error_message = "このメールはすでに存在します。別のメールをお試しください。"
                return render(request, 'home/add-user.html', {'form': form, 'error_message': error_message})
            form.save()
            update_success_message = 'ユーザー詳細が正常に更新されました'
            messages.success(request, update_success_message)
            return redirect('/user_list')

    else:
        form = UserAddForm(instance=user)
    context = {"form": form, "show": show}
    return render(request, 'home/add-user.html', context)


# Delete user api
def delete_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Extract the user_id from the request data
        user_id = data.get('user_id')
        if user_id:
            # Assuming your model is named 'User'
            user = get_object_or_404(User, pk=user_id)
            user.isDeleted = True
            user.save()
            response_data = {'message': 'ユーザー削除成功されました。'}
            return JsonResponse(response_data, status=200)
        else:
            response_data = {'error': 'ユーザーIDが提供されていないです。'}
            return JsonResponse(response_data, status=400)
    else:
        return JsonResponse({'error': '無効なリクエストメソッド'}, status=400)


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
    context={}
    html_template = loader.get_template('home/add-house.html')
    return HttpResponse(html_template.render(context, request))

def  farm_manage (request):
    context={}
    html_template = loader.get_template('home/farm_manage.html')
    return HttpResponse(html_template.render(context, request))
def  reset_password (request):
    context={}
    html_template = loader.get_template('accounts/reset_password.html')
    return HttpResponse(html_template.render(context, request))


def add_plant(request):
    if request.method == "GET":
        form = PlantForm()
        return render(request, 'home/add-plant.html', {"form": form})
    else:
        form = PlantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/plant_setting')  # Redirect to a success page or the desired URL