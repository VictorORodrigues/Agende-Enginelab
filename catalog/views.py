from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from account.decorators import requer_admin, requer_permissao_subadmin, requer_subadm

from .forms import EquipamentoForm, LivroForm
from .models import Categoria, Emprestimo, Equipamento, FilaEspera, Livro


# ===============================
# EQUIPAMENTOS
# ===============================
@login_required
def equipamentos(request):
    qs = Equipamento.objects.select_related('categoria').all()
    categoria_id = request.GET.get('categoria')
    status = request.GET.get('status')
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if status:
        qs = qs.filter(status=status)

    context = {
        'equipamentos': qs,
        'categorias': Categoria.objects.all(),
        'status_choices': Equipamento.STATUS_CHOICES,
        'categoria_selecionada': categoria_id,
        'status_selecionado': status,
        'pode_gerenciar': request.user.perfil.tem_permissao('equipamento'),
        'minhas_filas_ids': set(
            FilaEspera.objects.filter(usuario=request.user).values_list('equipamento_id', flat=True)
        ),
    }
    return render(request, 'catalog/equipamentos.html', context)


@requer_permissao_subadmin('equipamento')
def equipamento_criar(request):
    if request.method == 'POST':
        form = EquipamentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipamento cadastrado.')
            return redirect(reverse('equipamentos'))
    else:
        form = EquipamentoForm()
    return render(request, 'catalog/equipamento_form.html', {'form': form, 'modo': 'criar'})


@requer_permissao_subadmin('equipamento')
def equipamento_editar(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    if request.method == 'POST':
        form = EquipamentoForm(request.POST, instance=equipamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipamento atualizado.')
            return redirect(reverse('equipamentos'))
    else:
        form = EquipamentoForm(instance=equipamento)
    return render(request, 'catalog/equipamento_form.html', {
        'form': form, 'modo': 'editar', 'equipamento': equipamento,
    })


@requer_admin
def equipamento_excluir(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    if request.method == 'POST':
        equipamento.delete()
        messages.success(request, 'Equipamento excluído.')
        return redirect(reverse('equipamentos'))
    return render(request, 'catalog/confirmar_exclusao.html', {'objeto': equipamento, 'tipo': 'equipamento'})


# ===============================
# LIVROS
# ===============================
@login_required
def livros(request):
    qs = Livro.objects.select_related('categoria').all()
    categoria_id = request.GET.get('categoria')
    status = request.GET.get('status')
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if status:
        qs = qs.filter(status=status)

    context = {
        'livros': qs,
        'categorias': Categoria.objects.all(),
        'status_choices': Livro.STATUS_CHOICES,
        'categoria_selecionada': categoria_id,
        'status_selecionado': status,
        'pode_gerenciar': request.user.perfil.tem_permissao('livro'),
    }
    return render(request, 'catalog/livros.html', context)


@requer_permissao_subadmin('livro')
def livro_criar(request):
    if request.method == 'POST':
        form = LivroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Livro cadastrado.')
            return redirect(reverse('livros'))
    else:
        form = LivroForm()
    return render(request, 'catalog/livro_form.html', {'form': form, 'modo': 'criar'})


@requer_permissao_subadmin('livro')
def livro_editar(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    if request.method == 'POST':
        form = LivroForm(request.POST, instance=livro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Livro atualizado.')
            return redirect(reverse('livros'))
    else:
        form = LivroForm(instance=livro)
    return render(request, 'catalog/livro_form.html', {'form': form, 'modo': 'editar', 'livro': livro})


@requer_admin
def livro_excluir(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    if request.method == 'POST':
        livro.delete()
        messages.success(request, 'Livro excluído.')
        return redirect(reverse('livros'))
    return render(request, 'catalog/confirmar_exclusao.html', {'objeto': livro, 'tipo': 'livro'})


# ===============================
# SOLICITAÇÕES DE EMPRÉSTIMO
# ===============================
def _notificar_admin_novo_emprestimo(emprestimo):
    html_message = render_to_string('emails/email_novo_emprestimo_admin.html', {'emprestimo': emprestimo})
    send_mail(
        'Nova solicitação de empréstimo - EngineLab',
        f'{emprestimo.usuario.get_full_name()} solicitou o empréstimo de {emprestimo.item}.',
        settings.DEFAULT_FROM_EMAIL,
        [settings.EMAIL_ADMIN_LAB],
        html_message=html_message,
    )


@login_required
def solicitar_emprestimo(request, eq_id):
    equipamento = get_object_or_404(Equipamento, pk=eq_id)
    if request.method == 'POST':
        emprestimo = Emprestimo.objects.create(
            usuario=request.user,
            equipamento=equipamento,
            data_final=request.POST.get('data_final'),
        )
        _notificar_admin_novo_emprestimo(emprestimo)
        messages.success(request, 'Solicitação de empréstimo enviada. Aguarde a aprovação.')
        return redirect(reverse('meus_emprestimos'))
    return render(request, 'catalog/confirmar_solicitacao.html', {'item': equipamento, 'tipo': 'equipamento'})


@login_required
def solicitar_livro(request, livro_id):
    livro = get_object_or_404(Livro, pk=livro_id)
    if request.method == 'POST':
        emprestimo = Emprestimo.objects.create(
            usuario=request.user,
            livro=livro,
            data_final=request.POST.get('data_final'),
        )
        _notificar_admin_novo_emprestimo(emprestimo)
        messages.success(request, 'Solicitação de empréstimo enviada. Aguarde a aprovação.')
        return redirect(reverse('meus_emprestimos'))
    return render(request, 'catalog/confirmar_solicitacao.html', {'item': livro, 'tipo': 'livro'})


# ===============================
# FILA DE ESPERA (apenas equipamentos por enquanto)
# ===============================
@login_required
def fila_espera(request):
    minhas_filas = FilaEspera.objects.filter(usuario=request.user).select_related('equipamento', 'livro')
    entradas = []
    for fila in minhas_filas:
        if fila.equipamento_id:
            posicao = FilaEspera.objects.filter(
                equipamento=fila.equipamento, data_solicitacao__lte=fila.data_solicitacao
            ).count()
        else:
            posicao = FilaEspera.objects.filter(
                livro=fila.livro, data_solicitacao__lte=fila.data_solicitacao
            ).count()
        entradas.append({'fila': fila, 'posicao': posicao})
    return render(request, 'catalog/fila_espera.html', {'entradas': entradas})


@login_required
def entrar_fila(request, eq_id):
    equipamento = get_object_or_404(Equipamento, pk=eq_id)
    if request.method == 'POST':
        if FilaEspera.objects.filter(usuario=request.user, equipamento=equipamento).exists():
            messages.info(request, 'Você já está na fila de espera deste equipamento.')
        else:
            FilaEspera.objects.create(usuario=request.user, equipamento=equipamento)
            messages.success(request, 'Você entrou na fila de espera.')
    return redirect(reverse('equipamentos'))


@login_required
def sair_fila(request, fila_id):
    fila = get_object_or_404(FilaEspera, pk=fila_id, usuario=request.user)
    if request.method == 'POST':
        fila.delete()
        messages.success(request, 'Você saiu da fila de espera.')
    return redirect(reverse('fila_espera'))


# ===============================
# MEUS EMPRÉSTIMOS
# ===============================
@login_required
def meus_emprestimos(request):
    emprestimos = Emprestimo.objects.filter(usuario=request.user).select_related('equipamento', 'livro')
    contadores = {status: emprestimos.filter(status=status).count() for status, _ in Emprestimo.STATUS_CHOICES}
    return render(request, 'catalog/meus_emprestimos.html', {
        'emprestimos': emprestimos, 'contadores': contadores,
    })


# ===============================
# ADMIN — EMPRÉSTIMOS
# ===============================
@requer_subadm
def admin_emprestimos(request):
    qs = Emprestimo.objects.select_related('usuario', 'equipamento', 'livro').all()
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    return render(request, 'catalog/admin_emprestimos.html', {
        'emprestimos': qs, 'status_choices': Emprestimo.STATUS_CHOICES, 'status_selecionado': status,
    })


@requer_subadm
def aprovar_emprestimo(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk, status=Emprestimo.STATUS_PENDENTE)
    if request.method == 'POST':
        emprestimo.status = Emprestimo.STATUS_ATIVO
        emprestimo.save()

        item = emprestimo.item
        item.status = item.STATUS_EMPRESTADO
        item.save()

        html_message = render_to_string('emails/email_emprestimo_aprovado.html', {'emprestimo': emprestimo})
        send_mail(
            'Empréstimo aprovado - EngineLab',
            f'Seu empréstimo de {item} foi aprovado.',
            settings.DEFAULT_FROM_EMAIL,
            [emprestimo.usuario.email],
            html_message=html_message,
        )
        messages.success(request, 'Empréstimo aprovado.')
    return redirect(reverse('admin_emprestimos'))


@requer_subadm
def reprovar_emprestimo(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk, status=Emprestimo.STATUS_PENDENTE)
    if request.method == 'POST':
        emprestimo.status = Emprestimo.STATUS_REJEITADO
        emprestimo.save()

        html_message = render_to_string('emails/email_emprestimo_recusado.html', {'emprestimo': emprestimo})
        send_mail(
            'Empréstimo não aprovado - EngineLab',
            f'Seu pedido de empréstimo de {emprestimo.item} não foi aprovado.',
            settings.DEFAULT_FROM_EMAIL,
            [emprestimo.usuario.email],
            html_message=html_message,
        )
        messages.success(request, 'Empréstimo recusado.')
    return redirect(reverse('admin_emprestimos'))


@requer_subadm
def finalizar_emprestimo(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk, status=Emprestimo.STATUS_ATIVO)
    if request.method == 'POST':
        emprestimo.status = Emprestimo.STATUS_FINALIZADO
        emprestimo.save()

        item = emprestimo.item
        item.status = item.STATUS_DISPONIVEL
        item.save()

        if emprestimo.equipamento_id:
            proxima = FilaEspera.objects.filter(equipamento=emprestimo.equipamento).order_by('data_solicitacao').first()
        else:
            proxima = FilaEspera.objects.filter(livro=emprestimo.livro).order_by('data_solicitacao').first()

        if proxima:
            html_message = render_to_string('emails/email_fila_disponivel.html', {'item': item, 'fila': proxima})
            send_mail(
                'Item disponível - EngineLab',
                f'O item {item} que você aguardava na fila está disponível.',
                settings.DEFAULT_FROM_EMAIL,
                [proxima.usuario.email],
                html_message=html_message,
            )
        messages.success(request, 'Empréstimo finalizado.')
    return redirect(reverse('admin_emprestimos'))
