from django.contrib import admin
from django.urls import path, include
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
    path('accounts/', include('django.contrib.auth.urls')),
    path('account/', include('account.urls')), 
    path('appointment/', include('appointment.urls')),
]