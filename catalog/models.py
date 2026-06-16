from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Equipamento(models.Model):
    STATUS_DISPONIVEL = 'disponivel'
    STATUS_EMPRESTADO = 'emprestado'

    STATUS_CHOICES = [
        (STATUS_DISPONIVEL, 'Disponível'),
        (STATUS_EMPRESTADO, 'Emprestado'),
    ]

    nome = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='equipamentos')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DISPONIVEL)
    identificador = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.identificador})'


class Livro(models.Model):
    STATUS_DISPONIVEL = 'disponivel'
    STATUS_EMPRESTADO = 'emprestado'

    STATUS_CHOICES = [
        (STATUS_DISPONIVEL, 'Disponível'),
        (STATUS_EMPRESTADO, 'Emprestado'),
    ]

    titulo = models.CharField(max_length=150)
    autor = models.CharField(max_length=150)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='livros')
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DISPONIVEL)
    exemplares = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return f'{self.titulo} - {self.autor}'


class Emprestimo(models.Model):
    STATUS_PENDENTE = 'pendente'
    STATUS_ATIVO = 'ativo'
    STATUS_FINALIZADO = 'finalizado'
    STATUS_REJEITADO = 'rejeitado'

    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_ATIVO, 'Ativo'),
        (STATUS_FINALIZADO, 'Finalizado'),
        (STATUS_REJEITADO, 'Rejeitado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emprestimos')
    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.CASCADE, related_name='emprestimos', null=True, blank=True
    )
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='emprestimos', null=True, blank=True)
    data_inicio = models.DateField(auto_now_add=True)
    data_final = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)

    class Meta:
        ordering = ['-data_inicio']

    def __str__(self):
        return f'{self.usuario} - {self.item} ({self.status})'

    @property
    def item(self):
        return self.equipamento or self.livro

    def clean(self):
        if bool(self.equipamento_id) == bool(self.livro_id):
            raise ValidationError('Selecione exatamente um item: equipamento ou livro.')


class FilaEspera(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='filas_espera')
    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.CASCADE, related_name='fila_espera', null=True, blank=True
    )
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='fila_espera', null=True, blank=True)
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_solicitacao']

    def __str__(self):
        return f'{self.usuario} - {self.item}'

    @property
    def item(self):
        return self.equipamento or self.livro

    def clean(self):
        if bool(self.equipamento_id) == bool(self.livro_id):
            raise ValidationError('Selecione exatamente um item: equipamento ou livro.')
