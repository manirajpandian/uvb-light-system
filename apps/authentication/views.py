# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.models import User
from django.contrib import messages
import uuid
from apps.authentication.models import Profile, Company, Farm, House
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .helpers import send_forgot_password_mail, add_new_user_mail
import datetime
from django.utils import timezone
from django.db.models import Q
import random

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    loading = False
    
    if request.method == "POST": 
        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Check if the user with the given email exists
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                user_obj = None

            if user_obj:
                # User with the given email exists
                profile_obj = Profile.objects.get(user=user_obj)

                if profile_obj.username == username:
                    # Authenticate the user
                    user = authenticate(request, username=user_obj.username, email=email, password=password)

                    if user is not None:
                        login(request, user)
                        # Store the user's profile image URL in the session
                        request.session['user_profile_image'] = user.profile.image.url if user.profile.image else None

                        return redirect("/")
                    else:
                        msg = 'メールやパスワードが間違っています'
                else:
                    msg = 'IDまたはメールが間違っています'
            else:
                msg = 'IDまたはメールが間違っています'
        # else:
        #     msg = 'フォームが有効ではありません'

    forgot_password_message = request.session.pop('forgot_password_message', None)
    forgot_password_success_msg = request.session.pop('forgot_password_success_msg', None)
    email = request.session.pop('email',None)
    return render(request, "accounts/login.html", {"form": form, "msg": msg,'forgot_password_message': forgot_password_message, 'forgot_password_success_msg':forgot_password_success_msg, 'email':email, 'loading':loading})

# user list and active/disable
@login_required(login_url="/login/")
def user_list(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    user_company = request.session.get('user_company')
    current_user = request.user.id
    try:
        if user_role_id == '0':
            profile_list = Profile.objects.filter(Q(role_id='0'))
            user_profile_list = [(profile.user, profile) for profile in profile_list]
        else:
            profile_list = Profile.objects.filter(Q(user=current_user) | Q(mapped_under=current_user))
            user_profile_list = [(profile.user, profile) for profile in profile_list]
        paginator = Paginator(user_profile_list, 5)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)

        context = {'page': page, 
                   'user_profile_list': user_profile_list,
                   'user_profile_image': user_profile_image,
                    'user_role_id':user_role_id,
                    'user_company':user_company,
                    'current_user_id': request.user.id,
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

                update_success_message = f'{user_obj.first_name}の情報が正常に更新されました'
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
    user_company = request.session.get('user_company')
    try:
        user_obj = get_object_or_404(User, id=pk)
        profile_obj = get_object_or_404(Profile, user_id=pk)

        if request.method == 'POST':
            # Update user data
            user_obj.first_name = request.POST.get('first_name')
            user_obj.save()

            # Update profile data
            profile_obj.role_id = request.POST.get('role_id')
            profile_obj.address = request.POST.get('address')
            profile_obj.save()

            update_success_message = f'{user_obj.first_name}情報が正常に更新されました'
            messages.success(request, update_success_message)
            return redirect('/user_list')

        context = {
            'user_obj': user_obj,
            'show': 'true',
            'first_name': user_obj.first_name,
            'role_id': profile_obj.role_id,
            'address':profile_obj.address,
            'user_profile_image': user_profile_image,
            'user_role_id':user_role_id,
            'user_company':user_company,
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
    user_company = request.session.get('user_company')
    loading = False
    try:
        if request.method == "GET":
            context = {
                    'user_profile_image': user_profile_image,
                    'user_role_id':user_role_id,
                    'user_company':user_company,
                    'loading':loading,
                    'address_block':'none'
                    }
            return render(request, 'home/add-user.html', context)
        else:
            first_name = request.POST['first_name']
            email = request.POST['email']
            role_id = request.POST['role_id']
            user_id = request.user.id
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
                    'user_company':user_company,
                    'error_message':"このメールはすでに存在します。別のメールをお試しください。",
                    'loading':loading,
                    'address_block':'block'
                }
                return render(request, 'home/add-user.html', context)
            
            
            user_obj = get_object_or_404(User, id=user_id)
            company_id = user_obj.username
            company_obj = get_object_or_404(Company, user_id=user_id)
            user_company_name = company_obj.company_name
            user_company_address = company_obj.company_address
            def generate_farm_id():
                return "UVB" + ''.join(str(random.randint(0, 9)) for _ in range(6))

            def generate_unique_farm_id(existing_ids):
                new_farm_id = generate_farm_id()
                while new_farm_id in existing_ids:
                    new_farm_id = generate_farm_id()
                return new_farm_id

            existing_farm_ids = set()

            if role_id == '0':
                farm_id = generate_unique_farm_id(existing_farm_ids)
                existing_farm_ids.add(farm_id)
            else:
                farm_id = company_id
            
            token = str(uuid.uuid4())

            # mail sending fuction 
            add_new_user_mail(email, farm_id, token)

            if role_id == '0':
                user_obj = User(username = farm_id, first_name = first_name, email = email, is_active=False, is_superuser=True)
                user_obj.set_password('Test@123')
                user_obj.save()
            else:
                user_obj = User(username = str(uuid.uuid4())[:9].replace('-', '').upper(), first_name = first_name, email = email, is_active=False)
                user_obj.set_password('Test@123')
                user_obj.save()

            profile_obj = Profile.objects.create(user = user_obj, role_id = role_id, mapped_under = request.user.id, forget_password_token = token, token_expiration_time = expiration_time, username = farm_id)
            profile_obj.save()

            company_obj = Company.objects.create(user = user_obj, company_name = user_company_name, company_address = user_company_address)
            company_obj.save()

            loading = False
            success_message = f'{first_name}が正常に追加されました'
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

            user_obj.delete()
            profile_obj.delete()

            user_delete_success = 'ユーザーが正常に削除されました。' 
            messages.success(request, user_delete_success)
            return redirect('/user_list')
        else:
            user_delete_success = f'{ user_obj.first_name }が提供されていないです。'  
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
                request.session['forgot_password_message'] = 'このメールが存在しません'
                return redirect('/forgot_password/')
            
            user_obj = User.objects.get(email=email)
            token = str(uuid.uuid4())
            
            # Set expiration time for the token (24 hours from now)
            expiration_time = timezone.now() + datetime.timedelta(hours=24)

            profile_obj = Profile.objects.get(user=user_obj)
            farm_id = profile_obj.username
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
    user_company = request.session.get('user_company')
    context={
        'user_profile_image': user_profile_image,
        'user_role_id':user_role_id,
        'user_company':user_company,
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
            'user_role_id':user_role_id,
            'user_company':user_company,
        }

        if request.method == 'POST':
            image = request.FILES.get('profile_image')
            first_name = request.POST.get('first_name')
            password = request.POST.get('password')
            
            if not first_name:
                update_message = '氏名を入力してください'
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

# farmer list 
@login_required(login_url="/login/")
def farmer_list(request):
    try:
        user_profile_image = request.session.get('user_profile_image')
        user_role_id = request.session.get('role_id')
        user_company = request.session.get('user_company')
        company_obj = Company.objects.select_related('user__profile').order_by('id')
        profile_obj = Profile.objects.order_by('id')

        # Filter companies based on profile role_id
        company_list = [(company.user, company) for company in company_obj if company.user.profile.role_id == '1']

        # Paginate the filtered company list
        paginator = Paginator(company_list, 5)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)
        loading = False
        context = {'user_profile_image': user_profile_image,
            'user_role_id':user_role_id,
            'user_company':user_company,
            'loading':loading,
            'company_list':company_list,
            'page':page
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
                   active_user_obj = get_object_or_404(User, id=obj.user_id)
                   active_user_obj.is_active = is_active
                   active_user_obj.save()
                farm_obj = Farm.objects.filter(user_id=user_id)
                for farm in farm_obj:
                    house_obj = House.objects.filter(farm_id = farm.farm_id)
                    for house in house_obj:
                        house.is_active = is_active
                        house.save()
                       
                    farm.is_active = is_active
                    farm.save()
                   

                update_success_message = f'{user_obj.first_name}の情報が正常に更新されました'
                messages.success(request, update_success_message)
                return redirect('/farmer_list')

            except User.DoesNotExist:
                messages.error(request, '指定されたユーザーは存在しません')
                return redirect('/farmer_list')

            except Profile.DoesNotExist:
                messages.error(request, '指定されたプロファイルは存在しません')
                return redirect('/farmer_list')
        return render(request, 'home/farmer-list.html',context)

    except Exception as e:
        print(e)
    return render(request, 'home/farmer-list.html')

# add new farmer 
@login_required(login_url="/login/")
def add_farmer(request):
    user_profile_image = request.session.get('user_profile_image')
    user_role_id = request.session.get('role_id')
    user_company = request.session.get('user_company')
    loading = False
    try:
        if request.method == 'POST':
            company_name = request.POST.get('company_name')
            user_name = request.POST.get('user_name')
            email = request.POST.get('email')
            address = request.POST.get('address')

            def generate_farm_id():
                return "UVB" + ''.join(str(random.randint(0, 9)) for _ in range(6))

            def generate_unique_farm_id(existing_ids):
                new_farm_id = generate_farm_id()
                while new_farm_id in existing_ids:
                    new_farm_id = generate_farm_id()
                return new_farm_id

            existing_farm_ids = set()

            farm_id = generate_unique_farm_id(existing_farm_ids)
            existing_farm_ids.add(farm_id)

            token = str(uuid.uuid4())
            expiration_time = timezone.now() + datetime.timedelta(hours=24)
            loading = True
            if User.objects.filter(email=email).exists():
                loading = False
                
                company_obj = Company.objects.select_related('user__profile').order_by('id')
                company_list = [(company.user, company) for company in company_obj if company.user.profile.role_id == '1']

                # Paginate the filtered company list
                paginator = Paginator(company_list, 5)
                page_number = request.GET.get('page')
                page = paginator.get_page(page_number)
                
                context = {
                    'email': email,
                    'company_name':company_name,
                    'user_name':user_name,
                    'address':address,
                    'user_profile_image': user_profile_image,
                    'user_role_id':user_role_id,
                    'user_company':user_company,
                    'error_message':"このメールはすでに存在します。別のメールをお試しください。",
                    'loading':loading,
                    'show':'true',
                    'company_list':company_list,
                    'page':page
                }
                return render(request, 'home/farmer-list.html', context)
            # mail sending fuction 
            loading = True
            add_new_user_mail(email, farm_id, token)

            user_obj = User(username = farm_id, first_name = user_name, email = email, is_active=False)
            user_obj.set_password('Test@123')
            user_obj.save()

            profile_obj = Profile.objects.create(user = user_obj, role_id = '1', mapped_under = request.user.id, forget_password_token = token, token_expiration_time = expiration_time, username = farm_id)
            profile_obj.save()

            company_obj = Company.objects.create(user = user_obj, company_name = company_name, company_address = address)
            company_obj.save()
            loading = False
            message = '農家が正常に追加されました！'
            messages.success(request, message)
            return redirect('/farmer_list')
    except Exception as e:
        print(e)
    return render(request, 'home/farmer-list.html')

# delete farmer 
@login_required(login_url="/login/")
def delete_farmer(request, user_id):
    try:
        if request.method == 'POST':
            user_obj = get_object_or_404(User, id=user_id)
            profile_obj = get_object_or_404(Profile, user=user_obj)

            mapped_profile_obj = Profile.objects.filter(mapped_under=user_id)
            for obj in mapped_profile_obj:
                active_user_obj = User.objects.get(id=obj.user_id)
                active_user_obj.delete()
            
            farm_obj = Farm.objects.filter(user_id=user_id)
            for farm in farm_obj:
                house_obj = House.objects.filter(farm_id = farm.farm_id)
                for house in house_obj:
                    house.delete()
                farm.delete()

            company_obj = get_object_or_404(Company, user_id=user_id)
            company_obj.delete()
            profile_obj.delete()
            user_obj.delete()

            messages = '農家が正常に削除されました。' 
            messages.success(request, messages)
            return redirect('/farmer_list')
        else:
            messages = f'農家{ user_obj.first_name }が提供されていないです。'  
            messages.success(request, messages)
            return redirect('/farmer_list')

    except Exception as e:
        print(e)
    return redirect('/farmer_list')


# update farmer 
@login_required(login_url='/login/')
def update_farmer(request, user_id):
    try:
        if request.method == 'POST':
            # check if the user is already exist or not
            user_obj = get_object_or_404(User, id=user_id)
            company_obj = get_object_or_404(Company, user_id=user_id)
            company_name = request.POST.get('company_name')
            user_name = request.POST.get('user_name')
            address = request.POST.get('address')
            user_obj.first_name = user_name
            company_obj.company_name = company_name
            company_obj.company_address = address
            company_obj.save()
            user_obj.save()

            update_success_message = f'{company_obj.company_name}の情報が正常に更新されました'
            messages.success(request, update_success_message)
            return redirect('/farmer_list')

    except Exception as e:
        print('update farmer>>>',e)
    return redirect('/farmer_list')