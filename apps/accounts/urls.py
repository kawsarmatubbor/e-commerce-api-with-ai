from django.urls import path
from .views import (
    RegisterView, 
    OTPVerificationView, 
    ProfileView, 
    resend_account_verification_otp, 
    forgot_password_view, 
    SetNewPasswordView, 
    ChangePasswordView,
    notification_view,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', OTPVerificationView.as_view(), name='otp-verification'),
    path('account/resend-otp/', resend_account_verification_otp, name='resend-account-verification-otp'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/forgot/', forgot_password_view, name='forgot-password'),
    path('password/resend-otp/', forgot_password_view, name='resend-forgot-password-verification-otp'),
    path('password/reset/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('password/change/', ChangePasswordView.as_view(), name='set-new-password'),
    path('notifications/', notification_view, name='notifications'),
]