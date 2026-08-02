from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil, Setor, JurisdicaoSubAdmin

# --- CONFIGURAÇÃO DO PERFIL INLINE ---
class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Informações de Perfil'
    fk_name = 'user'
    fields = ('status', 'tipo', 'matricula', 'telefone')

# --- PERSONALIZAÇÃO DO USER ADMIN ---
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline, )
    
    # Exibe o tipo de usuário e setor diretamente na lista de usuários
    list_display = ('username', 'email', 'first_name', 'get_status', 'get_tipo', 'get_setores_gerenciados', 'is_active', 'is_staff')
    
    def get_tipo(self, instance):
        try:
            return instance.perfil.get_tipo_display()
        except:
            return "-"
    get_tipo.short_description = 'Tipo de Usuário'

    def get_status(self, instance):
        try:
            return instance.perfil.get_status_display()
        except:
            return "-"
    get_status.short_description = 'Status'

    def get_setores_gerenciados(self, instance):
        try:
            if instance.perfil.eh_subadm:
                setores = instance.perfil.setores_gerenciados.all()
                return ", ".join([s.nome for s in setores]) if setores else "Nenhum"
        except:
            pass
        return "-"
    get_setores_gerenciados.short_description = 'Setores Gerenciados'

# --- RE-REGISTRO DO MODELO USER ---
admin.site.unregister(User) # Remove o registro padrão
admin.site.register(User, UserAdmin) # Registra com a nossa customização

# --- REGISTRO DO SETOR ---
@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

# --- REGISTRO DA JURISDIÇÃO ---
@admin.register(JurisdicaoSubAdmin)
class JurisdicaoSubAdminAdmin(admin.ModelAdmin):
    list_display = ('subadmin', 'setor', 'pode_gerenciar_itens', 'pode_gerenciar_emprestimos')
    list_filter = ('setor', 'pode_gerenciar_itens', 'pode_gerenciar_emprestimos')

