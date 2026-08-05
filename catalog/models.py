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
    identificador = models.CharField(max_length=50, unique=True, verbose_name="Identificador")
    descricao = models.TextField(max_length=500, blank=True, null=True, verbose_name="Descrição")

    class Meta:
        ordering = ['nome']
        verbose_name = "Item"
        verbose_name_plural = "Itens"

    def __str__(self):
        return f'{self.nome} ({self.identificador})'

    def clean(self):
        if self.setor_id and self.categoria_id and self.categoria.setor_id != self.setor_id:
            raise ValidationError({'categoria': 'Esta categoria pertence a outro setor.'})

    def esta_disponivel(self, data=None):
        from datetime import date
        data = data or date.today()
        return not self.emprestimos.filter(
            status=Emprestimo.STATUS_ATIVO, data_inicio__lte=data, data_final__gte=data
        ).exists()

    def tem_emprestimo_ativo_ou_pendente(self):
        return self.emprestimos.filter(
            status__in=[Emprestimo.STATUS_PENDENTE, Emprestimo.STATUS_ATIVO]
        ).exists()

    @property
    def status(self):
        return self.STATUS_DISPONIVEL if self.esta_disponivel() else self.STATUS_EMPRESTADO

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


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
    exemplares = models.PositiveIntegerField(default=1, verbose_name="Exemplares")

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return f'{self.titulo} - {self.autor}'

    def clean(self):
        if self.setor_id and self.categoria_id and self.categoria.setor_id != self.setor_id:
            raise ValidationError({'categoria': 'Esta categoria pertence a outro setor.'})

    def esta_disponivel(self, data=None):
        from datetime import date
        data = data or date.today()
        return not self.emprestimos.filter(
            status=Emprestimo.STATUS_ATIVO, data_inicio__lte=data, data_final__gte=data
        ).exists()

    def tem_emprestimo_ativo_ou_pendente(self):
        return self.emprestimos.filter(
            status__in=[Emprestimo.STATUS_PENDENTE, Emprestimo.STATUS_ATIVO]
        ).exists()

    @property
    def status(self):
        return self.STATUS_DISPONIVEL if self.esta_disponivel() else self.STATUS_EMPRESTADO

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


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
        Equipamento, on_delete=models.SET_NULL, related_name='emprestimos', null=True, blank=True
    )
    livro = models.ForeignKey(Livro, on_delete=models.SET_NULL, related_name='emprestimos', null=True, blank=True)
    item_nome_snapshot = models.CharField(max_length=150, blank=True, verbose_name="Item (registro histórico)")
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Solicitação")
    data_inicio = models.DateField(verbose_name="Data de Início do Uso")
    data_final = models.DateField()
    dia_inteiro = models.BooleanField(default=True, verbose_name="Dia Inteiro")
    hora_inicio = models.TimeField(null=True, blank=True, verbose_name="Hora de Início")
    hora_fim = models.TimeField(null=True, blank=True, verbose_name="Hora de Fim")
    data_devolucao = models.DateField(null=True, blank=True, verbose_name="Data de Devolução Real")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    vezes_renovado = models.PositiveIntegerField(default=0, verbose_name="Vezes Renovado")
    token_acao = models.CharField(max_length=64, unique=True, null=True, blank=True)
    token_renovacao = models.CharField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        ordering = ['-data_inicio', '-id']

    def __str__(self):
        return f'{self.usuario} - {self.item_display} ({self.status})'

    def save(self, *args, **kwargs):
        item_atual = self.equipamento or self.livro
        if item_atual:
            self.item_nome_snapshot = str(item_atual)
        super().save(*args, **kwargs)

    @property
    def item(self):
        return self.equipamento or self.livro

    @property
    def item_display(self):
        return self.equipamento or self.livro or self.item_nome_snapshot or '(item removido)'

    def clean(self):
        from datetime import date, timedelta
        if bool(self.equipamento_id) == bool(self.livro_id):
            raise ValidationError('Selecione exatamente um item: equipamento ou livro.')

        if self.data_inicio and self.data_inicio < date.today():
            raise ValidationError('A data de início não pode ser no passado.')

        if self.data_final and self.data_inicio:
            if self.data_final < self.data_inicio:
                raise ValidationError('A data de devolução não pode ser anterior à data de início.')

            # Limita empréstimos a no máximo 1 mês (30 dias) a partir do início
            if self.data_final > self.data_inicio + timedelta(days=30):
                raise ValidationError('O período do empréstimo não pode ser superior a 1 mês.')

        if not self.dia_inteiro:
            if not self.hora_inicio or not self.hora_fim:
                raise ValidationError('Informe a hora de início e de fim, ou marque "Dia Inteiro".')
            if self.hora_inicio >= self.hora_fim:
                raise ValidationError('A hora de início deve ser anterior à hora de fim.')
