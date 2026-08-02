from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Setor(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    def __str__(self):
        return self.nome

class Perfil(models.Model):
    STATUS_PENDENTE = 'pendente'
    STATUS_APROVADO = 'aprovado'
    STATUS_REJEITADO = 'rejeitado'

    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_APROVADO, 'Aprovado'),
        (STATUS_REJEITADO, 'Rejeitado'),
    ]

    TIPO_USUARIO = [
        ('ALUNO', 'Aluno'),
        ('SUBADM', 'Sub-Administrador'),
        ('ADMIN', 'Administrador Geral'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO, default='ALUNO')
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    setores_gerenciados = models.ManyToManyField(Setor, blank=True, related_name='subadmins', through='JurisdicaoSubAdmin')
    token_aprovacao = models.CharField(max_length=64, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.user.is_superuser or self.user.is_staff:
            return
        should_be_active = self.status == self.STATUS_APROVADO
        if self.user.is_active != should_be_active:
            User.objects.filter(pk=self.user_id).update(is_active=should_be_active)
            self.user.is_active = should_be_active

    @property
    def eh_aluno(self):
        return self.tipo == 'ALUNO'

    @property
    def eh_subadm(self):
        return self.tipo == 'SUBADM'

    @property
    def eh_admin(self):
        return self.tipo == 'ADMIN'

    def tem_permissao(self, escopo):
        if self.eh_admin:
            return True
        if self.eh_subadm:
            if escopo == 'item':
                return self.jurisdicoes.filter(pode_gerenciar_itens=True).exists()
            if escopo == 'emprestimo':
                return self.jurisdicoes.filter(pode_gerenciar_emprestimos=True).exists()
            return self.setores_gerenciados.exists()
        return False

    def gerencia_setor(self, setor, permissao=None):
        if self.eh_admin:
            return True
        if self.eh_subadm:
            qs = self.jurisdicoes.filter(setor=setor)
            if permissao == 'item':
                return qs.filter(pode_gerenciar_itens=True).exists()
            if permissao == 'emprestimo':
                return qs.filter(pode_gerenciar_emprestimos=True).exists()
            return qs.exists()
        return False

    @property
    def pode_gerenciar_itens_geral(self):
        return self.tem_permissao('item')


class JurisdicaoSubAdmin(models.Model):
    subadmin = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='jurisdicoes')
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    pode_gerenciar_itens = models.BooleanField(default=False, verbose_name="Gerenciar Itens")
    pode_gerenciar_emprestimos = models.BooleanField(default=False, verbose_name="Gerenciar Empréstimos")

    class Meta:
        unique_together = ['subadmin', 'setor']

    def __str__(self):
        return f"{self.subadmin.user.email} no setor {self.setor.nome}"


# O modelo PermissaoSubAdmin antigo pode ser removido pois a nova lógica o substitui
# Vou apenas comentá-lo para evitar erros de importação imediatos se houver algum
# class PermissaoSubAdmin(models.Model): ...



# --- SIGNALS: Isto garante que o Perfil exista sempre ---
@receiver(post_save, sender=User)
def manage_user_perfil(sender, instance, created, **kwargs):
    if created:
        status = Perfil.STATUS_APROVADO if (instance.is_superuser or instance.is_staff) else Perfil.STATUS_PENDENTE
        Perfil.objects.create(user=instance, status=status)
    else:
        Perfil.objects.get_or_create(user=instance)
