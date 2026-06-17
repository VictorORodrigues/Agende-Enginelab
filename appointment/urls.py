from django.urls import path
from . import views

app_name = 'appointment'

urlpatterns = [
    path('', views.home, name='home'),
    path('meus-agendamentos/', views.meus_agendamentos, name='meus_agendamentos'),
    path('solicitar/', views.solicitar_agendamento, name='solicitar_agendamento'),
    path('cancelar/<int:pk>/', views.cancelar_agendamento, name='cancelar_agendamento'),
    path('gerenciar/', views.gerenciar_agendamentos, name='gerenciar_agendamentos'),
    path('aprovar/<int:pk>/', views.aprovar_agendamento, name='aprovar_agendamento'),
    path('recusar/<int:pk>/', views.recusar_agendamento, name='recusar_agendamento'),
]
