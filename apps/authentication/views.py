# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.models import User
from django.contrib import messages
import uuid
from django.conf import settings
from django.core.mail import send_mail
from .forms import NewUserAddForm

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    # print('users>>>',User.objects.all())
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


def new_add_user(request):
    try:
        if request.method == "GET":
            form = NewUserAddForm()
            print('>>>>>>>>')
            context = {"form": form}
            return render(request, 'home/add-user.html', context)
    except Exception as e:
        print(e)
    return render(request, 'home/add-user.html')


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

            # return redirect("/login/")

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