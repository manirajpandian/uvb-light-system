# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.models import User
from django.contrib import messages
import uuid
from django.conf import settings
from django.core.mail import send_mail
from .models import Profile
from django.core.paginator import Paginator

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            print(username, email, password)
            if User.objects.filter(email=email).exists():
                user = authenticate(request,username=username, email=email, password=password)
                if user is not None:
                    # Login the user
                    login(request, user)
                    return redirect("/")
                else:
                    msg = '無効な認証'
            else:
                msg = 'メールとユーザは存在しません'
        else:
            msg = 'バリデーションエラー'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})

# user list and active/disable function 

def admin_list(request):
    try:
        user_list = User.objects.all()
        profile_list = Profile.objects.filter(user__in=user_list)

        context = {'user_profile_list': zip(user_list, profile_list),}
        if request.method == "POST":
            user_id = request.POST['user_id']
            is_active = request.POST['is_active']
            print(user_id,'<<<<<<')
            print(is_active,'is_active')
            user = get_object_or_404(User, pk=user_id)
            print('user>>>>>',user)
            user.is_active = is_active
            print('user.is_active>>>>>',user.is_active)
            user.save()
            success_message = "ユーザーステータスの変更に成功しました"  # success message here
            return render(request, 'home/admin.html', context,{'success_message': success_message})
    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)
    return render(request, 'home/admin.html', context)

def new_add_user(request):
    try:
        if request.method == "GET":
            current_user_id = request.user.id 
            context = {'current_user_id':current_user_id}
            return render(request, 'home/add-user.html', context)
        else:
            username = request.POST['username']
            email = request.POST['email']
            role_id = request.POST['role_id']
            user_id = request.POST['mapped_under']
            base_url = settings.BASE_URL
            if User.objects.filter(email=email).exists():
                error_message = "このメールはすでに存在します。別のメールをお試しください。"
                return render(request, 'home/add-user.html', {'error_message': error_message})

            farm_id = str(uuid.uuid4())[:6].upper()
            token = str(uuid.uuid4())
            link = f'{base_url}change_password/{token}'
            subject = 'パスワードの設定'
            message = f'''
            光防除システム管理サイトログイン

            光防除システム管理サイトへようこそ！
            下記の「パスワードの設定」をクリックして進んでください。

            パスワードの設定：{link}

            ★！現段階ではまた登録は完了しておりません！★
            ※ご本人様確認のため、上記URLへ「24時間以内」にアクセスしアカウントの本登録を完了いただけますようお願いいたします。

            農場ID：{farm_id}
            ID：{email}

            ご不明な点がございましたら、このメールへご返信いただくか、
            info@beam~ までご連絡ください。'''
            
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]

            send_mail(subject, message, from_email, recipient_list)

            user_obj = User(username = farm_id, first_name = username, email = email, is_active=False)
            user_obj.set_password('Test@123')
            user_obj.save()

            profile_obj = Profile.objects.create(user = user_obj, role_id = role_id, mapped_under = user_id, forget_password_token = token)
            profile_obj.save()

            success_message = "ユーザが正常に追加されました"
            messages.success(request, success_message)
            return redirect('/user_list')
        
    except Exception as e:
        print(e)
    return render(request, 'home/add-user.html')


def change_password (request, token):
    context={}
    try:
        profile_obj = Profile.objects.filter(forget_password_token = token).first()
        context={ 'is_change_password_view': True, 'user_id': profile_obj.user.id }

        if request.method == 'POST':
            password = request.POST['password']
            confirm_password = request.POST['confirm_password']
            user_id = request.POST['user_id']

            if password != confirm_password:
                messages.success(request, 'password error')
                return redirect(f'/change_password/{token}')
            
            user_obj = User.objects.get(id=user_id)
            user_obj.set_password(password)
            user_obj.save()

            return redirect ('/login/')
    except Exception as e:
        print(e)
    return render(request, 'accounts/change_password.html',{'context':context})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please <a href="/login">login</a>.'
            success = True

        else:
            msg = 'Form is not valid'

    return render(request, "accounts/register.html", { "msg": msg, "success": success})


def ForgetPassword(request):
    try:
        if request.method == 'POST':
            email = request.POST.get("email")
            if not User.objects.filter(email=email).first():
                messages.error(request,"Email does not exist.")
                return redirect('/forget_password')
            user_obj = User.objects.get(email=email)
            reset_token = str(uuid.uuid4())
            link = f'https://uvb-beamtec.mosaique.link/reset_password{reset_token}'
            subject = 'パスワードの設定'
            message = f"こちらから新しいパスワードを設定できます。\n{link}"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]

            send_mail(subject, message, from_email, recipient_list)
            return True
    except Exception as e:
        print('Error',e)
    return render(request, 'accounts/reset_password.html')