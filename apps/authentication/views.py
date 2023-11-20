# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.models import User
# from apps.home.models import User

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
