from django.urls import path
from . import views

urlpatterns = [
    # Quando o usuário acessar a raiz do site, chama a view dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Rota para solicitar empréstimo (vamos usar depois)
    path('solicitar/<int:eq_id>/', views.solicitar_emprestimo, name='solicitar'),
]