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
    TIPO_USUARIO = [
        ('ALUNO', 'Aluno'),
        ('SUBADM', 'Sub-Administrador'),
        ('ADMIN', 'Administrador Geral'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO, default='ALUNO')
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_display()}"

# --- SIGNALS: Isto garante que o Perfil exista sempre ---
@receiver(post_save, sender=User)
def manage_user_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
    instance.perfil.save()