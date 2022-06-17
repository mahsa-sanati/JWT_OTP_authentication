from django.urls import path
from rest_framework_jwt.views import refresh_jwt_token

from .views import *

urlpatterns = [
    path('send_otp/', SendOtpView.as_view(), name='send_otp'),
    path('validate_otp/', VerifyOtpView.as_view(), name='validate_otp'),
    path('registration/', UserSignUpView.as_view(), name='register_user'),
    path('login_by_otp/', LoginByOtpView.as_view(), name='login2'),
    path('reset_password/', ChangeForgetPasswordView.as_view(), name='reset_password'),
    path('login_by_password/', LoginByPasswordView.as_view(), name='login'),
    path('refresh_token/', refresh_jwt_token, name='refresh_token'),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),
    path('user_list/', UserListView.as_view(), name='user_list'),
    path('profile/<slug>/', ProfileView.as_view(), name='profile'),
]


