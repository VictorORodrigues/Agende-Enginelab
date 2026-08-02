from django.urls import path

from . import views

urlpatterns = [
    path('setor/<int:setor_id>/', views.itens_setor, name='itens_setor'),
    path('equipamentos/', views.equipamentos, name='equipamentos'),
    path('equipamentos/gerenciar/', views.admin_equipamentos, name='admin_equipamentos'),
    path('equipamentos/criar/', views.equipamento_criar, name='equipamento_criar'),
    path('equipamentos/<int:pk>/editar/', views.equipamento_editar, name='equipamento_editar'),
    path('equipamentos/<int:pk>/excluir/', views.equipamento_excluir, name='equipamento_excluir'),

    path('categorias/criar/', views.categoria_criar, name='categoria_criar'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/excluir/', views.categoria_excluir, name='categoria_excluir'),

    path('livros/', views.livros, name='livros'),
    path('livros/criar/', views.livro_criar, name='livro_criar'),
    path('livros/<int:pk>/editar/', views.livro_editar, name='livro_editar'),
    path('livros/<int:pk>/excluir/', views.livro_excluir, name='livro_excluir'),

    path('solicitar/equipamento/<int:eq_id>/', views.solicitar_emprestimo, name='solicitar_emprestimo'),
    path('solicitar/livro/<int:livro_id>/', views.solicitar_livro, name='solicitar_livro'),

    path('emprestimos/', views.meus_emprestimos, name='meus_emprestimos'),
    path('emprestimos/renovar/<int:pk>/', views.renovar_emprestimo, name='renovar_emprestimo'),

    # Fora do prefixo /admin/ para não colidir com o catch-all do
    # django.contrib.admin (path('admin/', admin.site.urls)).
    path('emprestimos/gerenciar/', views.admin_emprestimos, name='admin_emprestimos'),
    path('emprestimo/<int:pk>/aprovar/', views.aprovar_emprestimo, name='aprovar_emprestimo'),
    path('emprestimo/<int:pk>/reprovar/', views.reprovar_emprestimo, name='reprovar_emprestimo'),
    path('emprestimo/<int:pk>/finalizar/', views.finalizar_emprestimo, name='finalizar_emprestimo'),
    path('emprestimo/direto/<str:tipo>/<int:pk>/', views.emprestimo_direto, name='emprestimo_direto'),

    # Ações via token (e-mail)
    path('emprestimo/acao/aprovar/<str:token>/', views.aprovar_emprestimo_via_token, name='aprovar_emprestimo_via_token'),
    path('emprestimo/acao/recusar/<str:token>/', views.reprovar_emprestimo_via_token, name='reprovar_emprestimo_via_token'),
    path('emprestimo/acao/renovar/<str:token>/', views.renovar_emprestimo_via_token, name='renovar_emprestimo_via_token'),
]
