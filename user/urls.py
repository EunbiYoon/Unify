from django.urls import path
from .views import accountView, customloginView, registerView, logoutView
from django.contrib.auth import views as auth_views

urlpatterns = [
    #users
    path('',accountView, name="account_url"),
    path('login',customloginView, name='login_url'),
    path('register/',registerView, name="register_url"),
    path('logout/',logoutView, name="logout_url"),

    # reset process -> login.html
    path('login_password/', auth_views.PasswordResetView.as_view(), name='password_reset'),

    # after the password reset email sent -> email_sent.html
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),

    # password reset form in email link -> link_confirm.html
    path('email_reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # password is successfully reset in email link -> link_complete.html
    path('email_reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

]
