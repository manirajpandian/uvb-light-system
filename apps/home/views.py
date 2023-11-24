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
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.utils.html import format_html

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
    html_template = loader.get_template('home/switch.html')
    return HttpResponse(html_template.render(context, request))

def plant_setting(request):
    try:
        plant_list = Plant.objects.all().order_by('plant_id')
        page = Paginator(plant_list, 5)
        page_list = request.GET.get('page')
        page = page.get_page(page_list)
        context = {'segment':'plant_settings', 'plant_list': plant_list,'page': page}
        print('context>>>>',context)
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

# Add new user

@login_required
def add_user(request):
    if request.method == 'GET':
        context = {}
        return render(request, 'home/add-user.html', context)
    else:
    #     # form = UserAddForm(request.POST)
    
        username = request.POST['username']
        email = request.POST['email']
        print('email>>',email)
        print('username>>',username)
    #     user_id = request.POST['mapped_under']
    #     print('request>>>>>',request.POST['email'])
    #     email = request.POST['email']
    #     user_id = request.user.id
    #     print('user_id',user_id)
    #     if form.is_valid():
    #         if User.objects.filter(email=email).exists():
    #             error_message = "このメールはすでに存在します。別のメールをお試しください。"
    #             return render(request, 'home/add-user.html', {'form': form, 'error_message': error_message}) # Redirect to the same page
    #         else:
    #                 form.save()
    #                 farm_id = str(uuid.uuid4())[:6].upper()
    #                 reset_token = str(uuid.uuid4())
    #                 link = f'https://uvb-beamtec.mosaique.link/reset_password{reset_token}'
    #                 subject = 'パスワードの設定'
    #                 message = f'''
    #                 光防除システム管理サイトログイン

    #                 光防除システム管理サイトへようこそ！
    #                 下記の「パスワードの設定」をクリックして進んでください。

    #                 パスワードの設定：{link}

    #                 ★！現段階ではまた登録は完了しておりません！★
    #                 ※ご本人様確認のため、上記URLへ「24時間以内」にアクセスしアカウントの本登録を完了いただけますようお願いいたします。

    #                 農場ID：{farm_id}
    #                 ID：{email}

    #                 ご不明な点がございましたら、このメールへご返信いただくか、
    #                 info@beam~ までご連絡ください。'''
                    
    #                 from_email = settings.EMAIL_HOST_USER
    #                 recipient_list = [email]

    #                 send_mail(subject, message, from_email, recipient_list)

    #                 success_message = "ユーザが正常に追加されました"
    #                 messages.success(request, success_message)
    #                 return redirect('/user_list')
        # else:
        #     # Handle the case when the form is not valid
        #     error_message = "無効なフォームデータです。フォームフィールドを確認して、もう一度やり直してください。"
        #     return render(request, 'home/add-user.html', {'form': form, 'error_message': error_message}) # Redirect to the same page


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
            return render(request, 'home/admin.html', {'page': page, 'success_message': success_message})
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
            # user.isDeleted = True
            user.delete()
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
    
