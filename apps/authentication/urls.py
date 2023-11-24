# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.urls import path
from .views import login_view, register_user, add_user, change_password, user_list, update_user, delete_user, forgot_password, user_profile
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('add_user', add_user, name="add_user"),
    path('user_list', user_list, name='user_list'),
    path('update_user/<str:pk>',update_user,name='update_user'), 
    path('delete_user/<str:user_id>/', delete_user, name='delete_user'),
    path('forgot_password', forgot_password, name="forgot_password"),
    path('change_password/<str:token>', change_password, name="change_password"),
    path('user_profile', user_profile, name="user_profile"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)