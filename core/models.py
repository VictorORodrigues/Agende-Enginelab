from django.db import models
# Create your models here.
from django.db import models
from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User

# --- ENTIDADE: CATEGORIA ---
# Agora você cria as categorias no banco de dados (Admin)
class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

# --- ENTIDADE: EQUIPAMENTO ---
class Equipamento(models.Model):
    STATUS = [('disponivel', 'Disponível'), ('emprestado', 'Emprestado')]
    
    nome = models.CharField(max_length=100)
    # Relaciona com Categoria. Se deletar a categoria, protege o equipamento.
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='equipamentos')
    status = models.CharField(max_length=20, choices=STATUS, default='disponivel')
    identificador = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.nome} ({self.identificador})"

# --- ENTIDADE: PERFIL ---
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricula = models.CharField(max_length=20, unique=True)
    eh_professor = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

# --- ENTIDADE: EMPRÉSTIMO ---
class Emprestimo(models.Model):
    STATUS_EMP = [
        ('pendente', 'Pendente'),
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
        ('rejeitado', 'Rejeitado'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE)
    data_inicio = models.DateField(auto_now_add=True)
    data_final = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_EMP, default='pendente')

# --- ENTIDADE: FILA DE ESPERA ---
class FilaEspera(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE)
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_solicitacao']