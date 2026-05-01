from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil, Setor

# --- CONFIGURAÇÃO DO PERFIL INLINE ---
class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Informações de Perfil'
    fk_name = 'user'

# --- PERSONALIZAÇÃO DO USER ADMIN ---
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline, )
    
    # Exibe o tipo de usuário e setor diretamente na lista de usuários
    list_display = ('username', 'email', 'first_name', 'get_tipo', 'get_setor', 'is_staff')
    
    def get_tipo(self, instance):
        return instance.perfil.get_tipo_display()
    get_tipo.short_description = 'Tipo de Usuário'

    def get_setor(self, instance):
        return instance.perfil.setor.nome if instance.perfil.setor else '-'
    get_setor.short_description = 'Setor/Categoria'

# --- RE-REGISTRO DO MODELO USER ---
admin.site.unregister(User) # Remove o registro padrão
admin.site.register(User, UserAdmin) # Registra com a nossa customização

# --- REGISTRO DO SETOR ---
@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)