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

    setor = models.ForeignKey(Setor, on_delete=models.PROTECT, related_name='agendamentos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agendamentos')
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    motivo = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-hora_inicio']

    def __str__(self):
        return f"{self.setor} — {self.data} {self.hora_inicio}"
