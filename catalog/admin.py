from django.contrib import admin

from .models import Categoria, Emprestimo, Equipamento, FilaEspera, Livro


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'identificador', 'categoria', 'status')
    list_filter = ('status', 'categoria')
    search_fields = ('nome', 'identificador')


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'categoria', 'status', 'exemplares')
    list_filter = ('status', 'categoria')
    search_fields = ('titulo', 'autor', 'isbn')


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'equipamento', 'livro', 'status', 'data_inicio', 'data_final')
    list_filter = ('status',)
    search_fields = ('usuario__username', 'usuario__first_name')


@admin.register(FilaEspera)
class FilaEsperaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'equipamento', 'livro', 'data_solicitacao')
    search_fields = ('usuario__username', 'usuario__first_name')
