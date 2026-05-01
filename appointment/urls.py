from django.urls import path
from . import views

# Definimos um namespace para facilitar o uso de {% url 'appointment:home' %}
app_name = 'appointment'

urlpatterns = [
    # Esta será a página inicial do sistema (localhost:8000/sistema/)
    path('', views.home, name='home'),
]