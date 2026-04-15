from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('emprestimo/aprovar/<int:pk>/', views.aprovar_emprestimo, name='aprovar_emprestimo'),
    path('emprestimo/reprovar/<int:pk>/', views.reprovar_emprestimo, name='reprovar_emprestimo'),
    path('solicitar/<int:eq_id>/', views.solicitar_emprestimo, name='solicitar'),
    path('accounts/ativar/<uidb64>/<token>/', views.ativar_conta, name='ativar_conta'),
    
    
]