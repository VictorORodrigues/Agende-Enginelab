from django.urls import path
from . import views

urlpatterns = [
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),

    # Gestão de usuários (admin)
    path('admin/usuarios/pendentes/', views.admin_usuarios_pendentes, name='admin_usuarios_pendentes'),
    path('admin/usuarios/aprovar/<int:pk>/', views.aprovar_usuario, name='aprovar_usuario'),
    path('admin/usuarios/recusar/<int:pk>/', views.recusar_usuario, name='recusar_usuario'),
    path('admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('admin/usuarios/alterar-status/<int:pk>/', views.alterar_status_usuario, name='alterar_status_usuario'),

    # Gestão de subadmins (admin)
    path('admin/subadmins/', views.admin_subadmins, name='admin_subadmins'),
    path('admin/subadmins/criar/', views.criar_subadmin, name='criar_subadmin'),
    path('admin/subadmins/<int:pk>/editar/', views.editar_subadmin, name='editar_subadmin'),
    path('admin/subadmins/<int:pk>/excluir/', views.excluir_subadmin, name='excluir_subadmin'),

    # Gestão de setores (admin)
    path('admin/setores/', views.admin_setores, name='admin_setores'),
    path('admin/setores/criar/', views.setor_criar, name='setor_criar'),
    path('admin/setores/<int:pk>/editar/', views.setor_editar, name='setor_editar'),
    path('admin/setores/<int:pk>/excluir/', views.setor_excluir, name='setor_excluir'),

    # Perfil
    path('perfil/excluir/', views.excluir_conta, name='excluir_conta'),

    # Ativação de SubAdmin
    path('subadmin/completar-perfil/<uidb64>/<token>/', views.completar_perfil_subadmin, name='completar_perfil_subadmin'),
]
