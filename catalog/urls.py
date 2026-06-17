from django.urls import path

from . import views

urlpatterns = [
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

    path('fila/', views.fila_espera, name='fila_espera'),
    path('fila/entrar/<int:eq_id>/', views.entrar_fila, name='entrar_fila'),
    path('fila/sair/<int:fila_id>/', views.sair_fila, name='sair_fila'),

    path('emprestimos/', views.meus_emprestimos, name='meus_emprestimos'),

    # Fora do prefixo /admin/ para não colidir com o catch-all do
    # django.contrib.admin (path('admin/', admin.site.urls)).
    path('emprestimos/gerenciar/', views.admin_emprestimos, name='admin_emprestimos'),
    path('emprestimo/<int:pk>/aprovar/', views.aprovar_emprestimo, name='aprovar_emprestimo'),
    path('emprestimo/<int:pk>/reprovar/', views.reprovar_emprestimo, name='reprovar_emprestimo'),
    path('emprestimo/<int:pk>/finalizar/', views.finalizar_emprestimo, name='finalizar_emprestimo'),
]
