from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=50, verbose_name="Nome")
    setor = models.ForeignKey('account.Setor', on_delete=models.CASCADE, related_name='categorias', verbose_name="Setor")
    descricao = models.TextField(max_length=300, blank=True, null=True, verbose_name="Descrição")

    class Meta:
        ordering = ['nome']
        unique_together = ['nome', 'setor']

    def __str__(self):
        return self.nome


class Equipamento(models.Model):
    STATUS_DISPONIVEL = 'disponivel'
    STATUS_EMPRESTADO = 'emprestado'

    STATUS_CHOICES = [
        (STATUS_DISPONIVEL, 'Disponível'),
        (STATUS_EMPRESTADO, 'Emprestado'),
    ]

    nome = models.CharField(max_length=100, verbose_name="Nome")
    setor = models.ForeignKey('account.Setor', on_delete=models.PROTECT, related_name='equipamentos', verbose_name="Setor", null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='equipamentos', verbose_name="Categoria")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DISPONIVEL, verbose_name="Status")
    identificador = models.CharField(max_length=50, unique=True, verbose_name="Identificador")
    descricao = models.TextField(max_length=500, blank=True, null=True, verbose_name="Descrição")

    class Meta:
        ordering = ['nome']
        verbose_name = "Item"
        verbose_name_plural = "Itens"

    def __str__(self):
        return f'{self.nome} ({self.identificador})'


class Livro(models.Model):
    STATUS_DISPONIVEL = 'disponivel'
    STATUS_EMPRESTADO = 'emprestado'

    STATUS_CHOICES = [
        (STATUS_DISPONIVEL, 'Disponível'),
        (STATUS_EMPRESTADO, 'Emprestado'),
    ]

    titulo = models.CharField(max_length=150, verbose_name="Título")
    autor = models.CharField(max_length=150, verbose_name="Autor")
    setor = models.ForeignKey('account.Setor', on_delete=models.PROTECT, related_name='livros', verbose_name="Setor", null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='livros', verbose_name="Categoria")
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="ISBN")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DISPONIVEL, verbose_name="Status")
    exemplares = models.PositiveIntegerField(default=1, verbose_name="Exemplares")

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
        (STATUS_ATIVO, 'Emprestado'),
        (STATUS_FINALIZADO, 'Devolvido'),
        (STATUS_REJEITADO, 'Rejeitado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emprestimos')
    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.CASCADE, related_name='emprestimos', null=True, blank=True
    )
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='emprestimos', null=True, blank=True)
    data_inicio = models.DateField(auto_now_add=True)
    data_final = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True, verbose_name="Data de Devolução Real")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    vezes_renovado = models.PositiveIntegerField(default=0, verbose_name="Vezes Renovado")
    token_acao = models.CharField(max_length=64, unique=True, null=True, blank=True)
    token_renovacao = models.CharField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        ordering = ['-data_inicio', '-id']

    def __str__(self):
        return f'{self.usuario} - {self.item} ({self.status})'

    @property
    def item(self):
        return self.equipamento or self.livro

    def clean(self):
        from datetime import date, timedelta
        if bool(self.equipamento_id) == bool(self.livro_id):
            raise ValidationError('Selecione exatamente um item: equipamento ou livro.')

        if self.data_final:
            if self.data_final < date.today():
                raise ValidationError('A data de devolução não pode ser no passado.')

            # Limita empréstimos a no máximo 1 mês (30 dias)
            if self.data_final > date.today() + timedelta(days=30):
                raise ValidationError('A data de devolução não pode ser superior a 1 mês a partir de hoje.')
