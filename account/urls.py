from django.urls import path
from . import views

urlpatterns = [
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),

    # Gestão de usuários (admin)
    path('admin/usuarios/pendentes/', views.admin_usuarios_pendentes, name='admin_usuarios_pendentes'),
    path('admin/usuarios/aprovar/<int:pk>/', views.aprovar_usuario, name='aprovar_usuario'),
    path('admin/usuarios/recusar/<int:pk>/', views.recusar_usuario, name='recusar_usuario'),
    path('admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),

    # Gestão de subadmins (admin)
    path('admin/subadmins/', views.admin_subadmins, name='admin_subadmins'),
    path('admin/subadmins/criar/', views.criar_subadmin, name='criar_subadmin'),
    path('admin/subadmins/<int:pk>/editar/', views.editar_subadmin, name='editar_subadmin'),
    path('admin/subadmins/<int:pk>/excluir/', views.excluir_subadmin, name='excluir_subadmin'),

    # Páginas de acervo (stubs — redireciona para em construção)
    path('equipamentos/', views.pagina_em_construcao, {'titulo': 'Equipamentos'}, name='equipamentos'),
    path('livros/', views.pagina_em_construcao, {'titulo': 'Livros'}, name='livros'),
    path('fila-espera/', views.pagina_em_construcao, {'titulo': 'Fila de espera'}, name='fila_espera'),
    path('meus-emprestimos/', views.pagina_em_construcao, {'titulo': 'Meus empréstimos'}, name='meus_emprestimos'),
    path('admin/emprestimos/', views.pagina_em_construcao, {'titulo': 'Gestão de empréstimos'}, name='admin_emprestimos'),
]
