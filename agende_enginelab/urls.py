"""
URL configuration for agende_enginelab project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core.views import registro #importe sua view de registro

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Importe as views prontas do Django
from core.views import registro

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Agora a raiz ('') é a tela de login nativa do Django
    path('', auth_views.LoginView.as_view(), name='login'), 
    
    path('accounts/registro/', registro, name='registro'),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Mude a dashboard para outra rota, ex: /home/ ou /dashboard/
    path('dashboard/', include('core.urls')), 
]

