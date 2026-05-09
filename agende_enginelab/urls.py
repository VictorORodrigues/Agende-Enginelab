from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from account.views import register
from account.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginForm 
    ), name='login'),

    path('register/', register, name='register'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'accounts/password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.txt',
            html_email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'accounts/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('account/', include('account.urls')), 
    path('appointment/', include('appointment.urls')),
]
