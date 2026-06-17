from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Setor(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
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
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name='responsaveis')
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
            return self.permissoes.filter(escopo=escopo).exists()  # via PermissaoSubAdmin.subadmin
        return False


class PermissaoSubAdmin(models.Model):
    ESCOPO_EQUIPAMENTO = 'equipamento'
    ESCOPO_LIVRO = 'livro'
    ESCOPO_AGENDAMENTO = 'agendamento'
    ESCOPO_EMPRESTIMO = 'emprestimo'

    ESCOPO_CHOICES = [
        (ESCOPO_EQUIPAMENTO, 'Equipamento'),
        (ESCOPO_LIVRO, 'Livro'),
        (ESCOPO_AGENDAMENTO, 'Agendamento'),
        (ESCOPO_EMPRESTIMO, 'Empréstimo'),
    ]

    subadmin = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='permissoes')
    escopo = models.CharField(max_length=20, choices=ESCOPO_CHOICES)

    class Meta:
        unique_together = ['subadmin', 'escopo']

    def __str__(self):
        return f"{self.subadmin} — {self.get_escopo_display()}"


# --- SIGNALS: Isto garante que o Perfil exista sempre ---
@receiver(post_save, sender=User)
def manage_user_perfil(sender, instance, created, **kwargs):
    if created:
        status = Perfil.STATUS_APROVADO if (instance.is_superuser or instance.is_staff) else Perfil.STATUS_PENDENTE
        Perfil.objects.create(user=instance, status=status)
    else:
        Perfil.objects.get_or_create(user=instance)
