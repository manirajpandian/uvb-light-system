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
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .helpers import send_forgot_password_mail

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
    forgot_password_message = request.session.pop('forgot_password_message', None)
    forgot_password_success_msg = request.session.pop('forgot_password_success_msg', None)
    email = request.session.pop('email',None)
    print('forgot_password_message',forgot_password_message)
    return render(request, "accounts/login.html", {"form": form, "msg": msg,'forgot_password_message': forgot_password_message, 'forgot_password_success_msg':forgot_password_success_msg, 'email':email})

# user list and active/disable
@login_required
def user_list(request):
    try:
        user_list = User.objects.all().order_by('id')
        profile_list = Profile.objects.filter(user__in=user_list)
        user_profile_list = list(zip(user_list, profile_list))

        paginator = Paginator(user_profile_list, 5)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)

        context = {'page': page, 'user_profile_list': user_profile_list}

        if request.method == "POST":
            user_id = request.POST.get('user_id')
            is_active = request.POST.get('is_active')
            user_obj = User.objects.get(id=user_id)
            user_obj.is_active = is_active
            user_obj.save()
            success_message = "ユーザーステータスの変更に成功しました"
            context.update({'user_profile_list': user_profile_list, 'success_message': success_message})
            return render(request, 'home/admin.html', context)

    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)

    return render(request, 'home/admin.html', context)



# update/edit user 
@login_required
def update_user(request, pk):
    try:
        user_obj = get_object_or_404(User, id=pk)
        profile_obj = get_object_or_404(Profile, user_id=pk)

        if request.method == 'POST':
            # Update user data
            user_obj.first_name = request.POST.get('first_name')
            user_obj.save()

            # Update profile data
            profile_obj.role_id = request.POST.get('role_id')
            profile_obj.save()

            update_success_message = 'ユーザー詳細が正常に更新されました'
            messages.success(request, update_success_message)
            return redirect('/user_list')

        context = {
            'user_obj': user_obj,
            'show': 'true',
            'first_name': user_obj.first_name,
            'role_id': profile_obj.role_id,
        }
        return render(request, 'home/add-user.html', context)

    except Exception as e:
        # Handle the exception
        error_message = f'An error occurred: {str(e)}'
        messages.error(request, error_message)
        return redirect('/user_list')

# add a new user 
@login_required
def add_user(request):
    current_user_id = request.user.id 
    try:
        if request.method == "GET":
            context = {'current_user_id':current_user_id}
            return render(request, 'home/add-user.html', context)
        else:
            first_name = request.POST['first_name']
            email = request.POST['email']
            role_id = request.POST['role_id']
            user_id = request.user.id
            base_url = settings.BASE_URL

            if User.objects.filter(email=email).exists():
                context = {
                    'first_name': first_name,
                    'email': email,
                    'role_id': role_id,
                    'user_id':user_id
                }

                error_message = "このメールはすでに存在します。別のメールをお試しください。"
                return render(request, 'home/add-user.html', {'error_message': error_message,"context":context})

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

            user_obj = User(username = farm_id, first_name = first_name, email = email, is_active=False)
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

# delete user 
@login_required
def delete_user(request, user_id):
    try:
        if request.method == 'POST':
            user_obj = get_object_or_404(User, id=user_id)
            profile_obj = get_object_or_404(Profile, user=user_obj)

            user_obj.delete()
            profile_obj.delete()
            user_delete_success = 'ユーザーが正常に削除されました。' 
            messages.success(request, user_delete_success)
            return redirect('/user_list')
        else:
            user_delete_success = 'ユーザーが提供されていないです。'  
            messages.success(request, user_delete_success)
            return redirect('/user_list')

    except Exception as e:
        print(e)
    return redirect('/user_list')

# change password 

def change_password (request, token):
    context={}
    try:
        profile_obj = Profile.objects.filter(forget_password_token = token).first()
        context={ 'is_change_password': True, 'user_id': profile_obj.user.id }

        if request.method == 'POST':
            password = request.POST['password']
            confirm_password = request.POST['confirm_password']
            user_id = request.POST['user_id']

            if user_id is None:
                messages.error(request, 'no user id found')
                return redirect(f'/change_password/{token}')
            
            if password != confirm_password:
                messages.error(request, 'password error')
                return redirect(f'/change_password/{token}')
            
            user_obj = User.objects.get(id=user_id)
            user_obj.set_password(password)
            user_obj.is_active = True
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


# forgot password 

def forgot_password(request):
    try:
        if request.method == 'POST':
            csrf_token = request.POST.get('csrfmiddlewaretoken', '')
            if not csrf_token or not request.META.get('CSRF_COOKIE'):
                request.session['forgot_password_message'] = 'CSRF token is missing or invalid'
                return render(request, 'error_page.html', {'error_message': 'CSRF token is missing or invalid'})

            email = request.POST.get("email")

            if not User.objects.filter(email=email).first():
                request.session['email'] = email
                request.session['forgot_password_message'] = 'メールが存在しません'
                return redirect('/forgot_password/')
            
            user_obj = User.objects.get(email=email)
            token = str(uuid.uuid4())
            profile_obj = Profile.objects.get(user=user_obj)
            profile_obj.forget_password_token = token
            profile_obj.save()
            send_forgot_password_mail(user_obj.email, token)
            request.session['forgot_password_success_msg'] = '入力したメールアドレスにメールが送信されました。'
            
            return redirect('/login/')

    except Exception as e:
        print('Error', e)
        request.session['forgot_password_message'] = 'エラーが発生しました。もう一度お試しください。'

    return redirect('/login/')


def user_profile(request):
    try:
        current_user_id = request.user.id
        user_obj = get_object_or_404(User, id=current_user_id)
        profile_obj, created = Profile.objects.get_or_create(user_id=current_user_id)
        
        role_mapping = {
            '0': 'BEAM TECH スーパー管理者',
            '1': '管理者',
        }
        role_id = role_mapping.get(profile_obj.role_id, 'ユーザー')

        context = {
            'first_name': user_obj.first_name,
            'id': user_obj.username,
            'email': user_obj.email,
            'role_id': role_id,
            'profile_image': profile_obj.image or None,
        }

        if request.method == 'POST':
            image = request.FILES.get('profile_image')
            username = request.POST.get('first_name')
            password = request.POST.get('password')
            
            if not username:
                update_message = '氏名は空であってはならない'
                messages.error(request, update_message)
                return redirect('/user_profile')
            elif not password:
                user_obj.username = username
            elif username and password:
                user_obj.username = username
                user_obj.set_password(password)
            user_obj.save()

            if image:
                profile_obj.image = image
                profile_obj.save()
                request.session['image_path'] = profile_obj.image.url
            update_message = 'プロフィールの更新に成功しました！'
            messages.success(request, update_message)
            return redirect('/user_profile')

    except Exception as e:
        print('Error', e)

    return render(request, 'home/page-user.html', {'context': context})

