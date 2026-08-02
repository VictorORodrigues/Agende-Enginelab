from django.db import models
from django.conf import settings
from account.models import Setor

class Agendamento(models.Model):
    STATUS_PENDENTE = 'PENDENTE'
    STATUS_APROVADO = 'APROVADO'
    STATUS_RECUSADO = 'RECUSADO'
    STATUS_CANCELADO = 'CANCELADO'

    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_APROVADO, 'Aprovado'),
        (STATUS_RECUSADO, 'Recusado'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agendamentos')
    setor = models.ForeignKey(Setor, on_delete=models.PROTECT, related_name='agendamentos')
    equipamento = models.ForeignKey('catalog.Equipamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='agendamentos')
    livro = models.ForeignKey('catalog.Livro', on_delete=models.SET_NULL, null=True, blank=True, related_name='agendamentos')
    data = models.DateField(verbose_name="Data de Início")
    data_final = models.DateField(verbose_name="Data de Devolução", null=True, blank=True)
    dia_inteiro = models.BooleanField(default=False, verbose_name="Dia Inteiro")
    hora_inicio = models.TimeField(verbose_name="Hora de Início", null=True, blank=True)
    hora_fim = models.TimeField(verbose_name="Hora de Fim", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-hora_inicio']
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"

    def __str__(self):
        return f"{self.usuario.username} - {self.setor.nome} ({self.data})"
