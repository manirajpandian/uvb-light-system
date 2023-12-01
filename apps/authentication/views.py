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
from .helpers import send_forgot_password_mail
import datetime
from django.utils import timezone
from django.db.models import Q

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    loading = False
    
    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            if User.objects.filter(username=username).exists():
                if User.objects.filter(email=email).exists():
                    user = authenticate(request,username=username, email=email, password=password)
                    if user is not None:
                        # Login the user
                        login(request, user)
                        session_profile_obj, created = Profile.objects.get_or_create(user_id=request.user.id)
                        if created:
                            session_profile_obj.created_at = timezone.now()
                            session_profile_obj.role_id = '0'
                            session_profile_obj.save()
                        request.session['user_profile_image'] = user.profile.image.url if user.profile.image else None
                        return redirect("/")
                    else:
                        msg = '無効な認証'
                else:
                    msg = 'メールが不正です'
            else:
                msg = ' 農場IDが不正です'
        else:
            msg = 'バリデーションエラー'
    forgot_password_message = request.session.pop('forgot_password_message', None)
    forgot_password_success_msg = request.session.pop('forgot_password_success_msg', None)
    email = request.session.pop('email',None)
    return render(request, "accounts/login.html", {"form": form, "msg": msg,'forgot_password_message': forgot_password_message, 'forgot_password_success_msg':forgot_password_success_msg, 'email':email, 'loading':loading})

# user list and active/disable
@login_required(login_url="/login/")
def user_list(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    current_user = request.user.id
    try:
        if user_role_id == '0':
            profile_list = Profile.objects.filter(Q(role_id='0') | Q(role_id='1'))
            user_profile_list = [(profile.user, profile) for profile in profile_list]
        else:
            profile_list = Profile.objects.filter(mapped_under=current_user)
            user_profile_list = [(profile.user, profile) for profile in profile_list]
        paginator = Paginator(user_profile_list, 5)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)

        context = {'page': page, 
                   'user_profile_list': user_profile_list,
                   'user_profile_image': user_profile_image,
                    'user_role_id':user_role_id,
                }

        if request.method == "POST":
            user_id = request.POST.get('user_id')
            is_active = request.POST.get('is_active')
            try:
                user_obj = User.objects.get(id=user_id)

                # Deactivate the main user
                user_obj.is_active = is_active
                user_obj.save()

                # Get all profile objects mapped under the user_id
                profile_obj = Profile.objects.filter(mapped_under=user_id)
                for obj in profile_obj:
                   active_user_obj = User.objects.get(id=obj.user_id)
                   active_user_obj.is_active = is_active
                   active_user_obj.save()

                update_success_message = 'ユーザー情報が正常に更新されました'
                messages.success(request, update_success_message)
                return redirect('/user_list')

            except User.DoesNotExist:
                messages.error(request, '指定されたユーザーは存在しません')
                return redirect('/user_list')

            except Profile.DoesNotExist:
                messages.error(request, '指定されたプロファイルは存在しません')
                return redirect('/user_list')

    except BrokenPipeError as e:
        print('exception BrokenPipeError', e)

    return render(request, 'home/admin.html', context)



# update/edit user 
@login_required(login_url="/login/")
def update_user(request, pk):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
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

            update_success_message = 'ユーザー情報が正常に更新されました'
            messages.success(request, update_success_message)
            return redirect('/user_list')

        context = {
            'user_obj': user_obj,
            'show': 'true',
            'first_name': user_obj.first_name,
            'role_id': profile_obj.role_id,
            'user_profile_image': user_profile_image,
            'user_role_id':user_role_id
        }
        return render(request, 'home/add-user.html', context)

    except Exception as e:
        # Handle the exception
        error_message = f'An error occurred: {str(e)}'
        messages.error(request, error_message)
        return redirect('/user_list')

# add a new user 
@login_required(login_url="/login/")
def add_user(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    loading = False
    try:
        if request.method == "GET":
            context = {
                    'user_profile_image': user_profile_image,
                    'user_role_id':user_role_id,
                    'loading':loading
                    }
            return render(request, 'home/add-user.html', context)
        else:
            first_name = request.POST['first_name']
            email = request.POST['email']
            role_id = request.POST['role_id']
            user_id = request.user.id
            base_url = settings.BASE_URL
            loading = True
            expiration_time = timezone.now() + datetime.timedelta(hours=24)

            if User.objects.filter(email=email).exists():
                loading = False
                context = {
                    'first_name': first_name,
                    'email': email,
                    'role_id': role_id,
                    'user_id':user_id,
                    'user_profile_image': user_profile_image,
                    'user_role_id':user_role_id,
                    'error_message':"このメールはすでに存在します。別のメールをお試しください。",
                    'loading':loading
                }
                return render(request, 'home/add-user.html', context)

            farm_id = "UVB" + str(uuid.uuid4())[:5].upper()
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

            if role_id == '0':
                user_obj = User(username = farm_id, first_name = first_name, email = email, is_active=False, is_superuser=True)
                user_obj.set_password('Test@123')
                user_obj.save()
            else:
                user_obj = User(username = farm_id, first_name = first_name, email = email, is_active=False)
                user_obj.set_password('Test@123')
                user_obj.save()

            profile_obj = Profile.objects.create(user = user_obj, role_id = role_id, mapped_under = request.user.id, forget_password_token = token, token_expiration_time = expiration_time)
            profile_obj.save()

            loading = False
            success_message = "ユーザが正常に追加されました"
            messages.success(request, success_message)
            return redirect('/user_list')
        
    except Exception as e:
        print(e)
    return render(request, 'home/add-user.html')

# delete user 
@login_required(login_url="/login/")
def delete_user(request, user_id):
    try:
        if request.method == 'POST':
            user_obj = get_object_or_404(User, id=user_id)
            profile_obj = get_object_or_404(Profile, user=user_obj)

            profile_obj = Profile.objects.filter(mapped_under=user_id)
            for obj in profile_obj:
                active_user_obj = User.objects.get(id=obj.user_id)
                active_user_obj.is_active = False
                active_user_obj.save()

            user_obj.delete()
            profile_obj.delete()
            user_delete_success = f'ユーザー{ user_obj.first_name }が正常に削除されました。' 
            messages.success(request, user_delete_success)
            return redirect('/user_list')
        else:
            user_delete_success = f'ユーザー{ user_obj.first_name }が提供されていないです。'  
            messages.success(request, user_delete_success)
            return redirect('/user_list')

    except Exception as e:
        print(e)
    return redirect('/user_list')


# change password 
def change_password(request, token):
    try:
        profile_obj = Profile.objects.filter(forget_password_token=token).first()

        if profile_obj is None:
            messages.error(request, 'Invalid or expired reset password link.')
            return redirect('/change_password/')  # Redirect to a suitable URL

        context = {'is_change_password': True, 'user_id': profile_obj.user.id}

        if request.method == 'POST':
            print('timezone.now()',timezone.now())
            print('profile_obj.token_expiration_time',profile_obj.token_expiration_time)
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            user_id = request.POST.get('user_id')

            if not user_id:
                messages.error(request, 'ユーザー ID が見つかりません。')
                return redirect(f'/change_password/{token}')

            if not (password and confirm_password):
                messages.error(request, 'パスワードと確認パスワードの両方を入力してください。')
                return redirect(f'/change_password/{token}')

            if password != confirm_password:
                messages.error(request, 'パスワードが一致しません。')
                return redirect(f'/change_password/{token}')

            if profile_obj.token_expiration_time and timezone.now() > profile_obj.token_expiration_time:
                messages.error(request, 'パスワード再設定リンクの有効期限が切れました。新しいパスワードを作成してください。')
                return redirect(f'/change_password/{token}')
            
            else:
                user_obj = User.objects.get(id=user_id)
                user_obj.set_password(password)
                user_obj.is_active = True
                user_obj.save()

                messages.success(request, 'パスワードの変更に成功しました。新しいパスワードでログインが可能です')
                return redirect('/login/')

    except Exception as e:
        print(e)
        messages.error(request, 'An error occurred. Please try again.')

    return render(request, 'accounts/change_password.html', {'context': context})


# forgot password 
def forgot_password(request):
    try:
        if request.method == 'POST':
            loading = True
            csrf_token = request.POST.get('csrfmiddlewaretoken', '')
            if not csrf_token or not request.META.get('CSRF_COOKIE'):
                request.session['forgot_password_message'] = 'CSRF token is missing or invalid'
                return render(request, 'error_page.html', {'error_message': 'CSRF token is missing or invalid'})

            email = request.POST.get("email")

            if not User.objects.filter(email=email).first():
                loading = False
                request.session['email'] = email
                request.session['forgot_password_message'] = 'メールが存在しません'
                return redirect('/forgot_password/')
            
            user_obj = User.objects.get(email=email)
            farm_id = "UVB" + str(uuid.uuid4())[:5].upper()
            token = str(uuid.uuid4())
            
            # Set expiration time for the token (24 hours from now)
            expiration_time = timezone.now() + datetime.timedelta(hours=24)

            user_obj.username = farm_id
            user_obj.save()

            profile_obj = Profile.objects.get(user=user_obj)
            profile_obj.forget_password_token = token
            profile_obj.token_expiration_time = expiration_time  # Save the expiration time
            profile_obj.save()
            
            send_forgot_password_mail(user_obj.email, token, farm_id)
            request.session['forgot_password_success_msg'] = '入力したメールアドレスにメールが送信されました。'

            loading = False
            
            return redirect('/login/')

    except Exception as e:
        print('Error', e)
        request.session['forgot_password_message'] = 'エラーが発生しました。もう一度お試しください。'
        loading = False
    return redirect('/login/')

@login_required(login_url="/login/")
def user_profile(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    context={
        'user_profile_image': user_profile_image,
        'user_role_id':user_role_id
        }
    try:
        current_user_id = request.user.id
        user_obj = get_object_or_404(User, id=current_user_id)
        profile_obj, created = Profile.objects.get_or_create(user_id=current_user_id)
        

        context = {
            'first_name': user_obj.first_name,
            'id': user_obj.username,
            'email': user_obj.email,
            'profile_image': profile_obj.image or None,
            'user_profile_image': user_profile_image,
            'user_role_id':user_role_id
        }

        if request.method == 'POST':
            image = request.FILES.get('profile_image')
            first_name = request.POST.get('first_name')
            password = request.POST.get('password')
            
            if not first_name:
                update_message = '氏名は空であってはならない'
                messages.error(request, update_message)
                return redirect('/user_profile')
            elif not password:
                user_obj.first_name = first_name
            elif first_name and password:
                user_obj.first_name = first_name
                user_obj.set_password(password)
            user_obj.save()

            if image:
                profile_obj.image = image
                profile_obj.save()
                request.session['user_profile_image'] = profile_obj.image.url
            update_message = 'プロフィールの更新に成功しました！'
            messages.success(request, update_message)
            return redirect('/user_profile')

    except Exception as e:
        print('Error', e)

    return render(request, 'home/page-user.html',  context)

