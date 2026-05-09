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
    STATUS_PENDENTE_EMAIL = 'PENDENTE_EMAIL'
    STATUS_PENDENTE_APROVACAO = 'PENDENTE_APROVACAO'
    STATUS_ATIVO = 'ATIVO'

    STATUS_CHOICES = [
        (STATUS_PENDENTE_EMAIL, 'Pendente de Confirmacao de E-mail'),
        (STATUS_PENDENTE_APROVACAO, 'Pendente de Aprovacao'),
        (STATUS_ATIVO, 'Ativo'),
    ]

    TIPO_USUARIO = [
        ('ALUNO', 'Aluno'),
        ('SUBADM', 'Sub-Administrador'),
        ('ADMIN', 'Administrador Geral'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDENTE_EMAIL)
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO, default='ALUNO')
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name='responsaveis')

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        should_be_active = self.status == self.STATUS_ATIVO
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

# --- SIGNALS: Isto garante que o Perfil exista sempre ---
@receiver(post_save, sender=User)
def manage_user_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
    else:
        Perfil.objects.get_or_create(user=instance)
