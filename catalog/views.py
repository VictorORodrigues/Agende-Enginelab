import secrets
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import ProtectedError, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.db import transaction
from datetime import date, timedelta

from account.decorators import requer_admin, requer_permissao_subadmin, requer_subadm
from account.models import Setor

from .forms import CategoriaForm, EquipamentoForm, LivroForm
from .models import Categoria, Emprestimo, Equipamento, Livro


# ===============================
# EQUIPAMENTOS
# ===============================
@login_required
def itens_setor(request, setor_id):
    setor = get_object_or_404(Setor, pk=setor_id)

    # Busca equipamentos e livros do setor
    equipamentos = list(Equipamento.objects.filter(setor=setor).select_related('categoria'))
    livros = list(Livro.objects.filter(setor=setor).select_related('categoria'))

    # Conecta tudo em uma única lista de itens
    todos_itens = []
    for eq in equipamentos:
        todos_itens.append({
            'obj': eq,
            'tipo': 'item',
            'nome': eq.nome,
            'id': eq.identificador,
            'cat': eq.categoria.nome,
            'cat_id': eq.categoria.pk,
            'status': eq.status
        })
    for liv in livros:
        todos_itens.append({
            'obj': liv,
            'tipo': 'livro',
            'nome': liv.titulo,
            'id': liv.isbn or '-',
            'cat': liv.categoria.nome,
            'cat_id': liv.categoria.pk,
            'status': liv.status
        })

    search_query = request.GET.get('q', '').lower()
    cat_filter = request.GET.get('categoria')
    status_filter = request.GET.get('status')

    # Filtra por Categoria (específica do setor)
    if cat_filter:
        todos_itens = [i for i in todos_itens if str(i['cat_id']) == cat_filter]

    # Filtra por Status
    if status_filter:
        todos_itens = [i for i in todos_itens if i['status'] == status_filter]

    # Filtra por Texto
    if search_query:
        todos_itens = [
            i for i in todos_itens
            if search_query in i['nome'].lower() or search_query in str(i['id']).lower() or search_query in i['cat'].lower()
        ]

    context = {
        'setor': setor,
        'itens': todos_itens,
        'categorias_do_setor': Categoria.objects.filter(setor=setor).order_by('nome'),
        'search_query': search_query,
        'categoria_selecionada': cat_filter,
        'status_selecionado': status_filter,
        'status_choices': Equipamento.STATUS_CHOICES,
        'meus_emprestimos_ids': set(
            Emprestimo.objects.filter(
                usuario=request.user,
                status__in=[Emprestimo.STATUS_PENDENTE, Emprestimo.STATUS_ATIVO]
            ).values_list('equipamento_id', flat=True)
        ) | set(
            Emprestimo.objects.filter(
                usuario=request.user,
                status__in=[Emprestimo.STATUS_PENDENTE, Emprestimo.STATUS_ATIVO]
            ).values_list('livro_id', flat=True)
        ),
        'eh_aluno': request.user.perfil.eh_aluno,
    }
    return render(request, 'catalog/itens_setor.html', context)


@login_required
def equipamentos(request):
    qs = Equipamento.objects.select_related('categoria').all()
    categoria_id = request.GET.get('categoria')
    status = request.GET.get('status')
    search_query = request.GET.get('q', '')

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if status:
        qs = qs.filter(status=status)
    if search_query:
        qs = qs.filter(
            Q(nome__icontains=search_query) |
            Q(identificador__icontains=search_query) |
            Q(categoria__nome__icontains=search_query)
        )

    context = {
        'equipamentos': qs,
        'categorias': Categoria.objects.all(),
        'status_choices': Equipamento.STATUS_CHOICES,
        'categoria_selecionada': categoria_id,
        'status_selecionado': status,
        'search_query': search_query,
        'pode_gerenciar': request.user.perfil.tem_permissao('equipamento'),
        'meus_emprestimos_ids': set(
            Emprestimo.objects.filter(
                usuario=request.user,
                status__in=[Emprestimo.STATUS_PENDENTE, Emprestimo.STATUS_ATIVO]
            ).values_list('equipamento_id', flat=True)
        ),
    }
    return render(request, 'catalog/equipamentos.html', context)


@requer_permissao_subadmin('item')
def admin_equipamentos(request):
    perfil = request.user.perfil
    qs = Equipamento.objects.select_related('categoria', 'setor').all()

    if perfil.eh_admin:
        setores_permitidos = Setor.objects.all()
    else:
        # Pega apenas setores onde ele pode gerenciar itens
        setores_permitidos = [jur.setor for jur in perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]
        qs = qs.filter(setor__in=setores_permitidos)

    categoria_id = request.GET.get('categoria')
    status = request.GET.get('status')
    search_query = request.GET.get('q', '')
    setor_id = request.GET.get('setor')

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if status:
        qs = qs.filter(status=status)
    if setor_id:
        qs = qs.filter(setor_id=setor_id)
    if search_query:
        qs = qs.filter(
            Q(nome__icontains=search_query) |
            Q(identificador__icontains=search_query) |
            Q(categoria__nome__icontains=search_query)
        )

    # CATEGORIAS
    if perfil.eh_admin:
        categorias_qs = Categoria.objects.all()
    else:
        categorias_qs = Categoria.objects.filter(setor__in=setores_permitidos)

    categorias_para_filtro = categorias_qs.order_by('nome')

    cat_q = request.GET.get('cat_q', '')
    cat_setor_id = request.GET.get('cat_setor')

    if cat_q:
        categorias_qs = categorias_qs.filter(nome__icontains=cat_q)
    if cat_setor_id:
        categorias_qs = categorias_qs.filter(setor_id=cat_setor_id)

    return render(request, 'catalog/admin_equipamentos.html', {
        'equipamentos': qs,
        'categorias': categorias_qs.annotate(total=Count('equipamentos')).order_by('nome'),
        'categorias_filtro': categorias_para_filtro,
        'status_choices': Equipamento.STATUS_CHOICES,
        'setores': setores_permitidos,
        'categoria_selecionada': categoria_id,
        'status_selecionado': status,
        'setor_selecionado': setor_id,
        'search_query': search_query,
        'cat_q': cat_q,
        'cat_setor_selecionado': cat_setor_id,
    })


@requer_permissao_subadmin('item')
def equipamento_criar(request):
    perfil = request.user.perfil
    if perfil.eh_admin:
        setores_permitidos = Setor.objects.all()
    else:
        setores_permitidos = [jur.setor for jur in perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]

    if not setores_permitidos:
        messages.error(request, "Você não tem permissão para gerenciar itens em nenhum setor.")
        return redirect('admin_equipamentos')

    tem_categorias = Categoria.objects.filter(setor__in=setores_permitidos).exists()
    if request.method == 'POST' and tem_categorias:
        form = EquipamentoForm(request.POST, user=request.user)
        if form.is_valid():
            # Segurança: verifica se o setor selecionado é permitido
            setor_escolhido = form.cleaned_data.get('setor')
            if not perfil.gerencia_setor(setor_escolhido, 'item'):
                messages.error(request, "Você não tem permissão para este setor.")
                return redirect('admin_equipamentos')

            form.save()
            messages.success(request, 'Item cadastrado.')
            return redirect(reverse('admin_equipamentos'))
    else:
        form = EquipamentoForm(user=request.user)
        # Filtra opções do form
        form.fields['setor'].queryset = Setor.objects.filter(id__in=[s.id for s in setores_permitidos])
        form.fields['categoria'].queryset = Categoria.objects.filter(setor__in=setores_permitidos)

    return render(request, 'catalog/equipamento_form.html', {
        'form': form,
        'modo': 'criar',
        'tem_categorias': tem_categorias
    })


@requer_permissao_subadmin('item')
def equipamento_editar(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    perfil = request.user.perfil

    if not perfil.gerencia_setor(equipamento.setor, 'item'):
        messages.error(request, "Você não tem permissão para editar itens deste setor.")
        return redirect('admin_equipamentos')

    if perfil.eh_admin:
        setores_permitidos = Setor.objects.all()
    else:
        setores_permitidos = [jur.setor for jur in perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]

    tem_categorias = Categoria.objects.filter(setor__in=setores_permitidos).exists()
    if request.method == 'POST':
        form = EquipamentoForm(request.POST, instance=equipamento, user=request.user)
        if form.is_valid():
            setor_escolhido = form.cleaned_data.get('setor')
            if not perfil.gerencia_setor(setor_escolhido, 'item'):
                messages.error(request, "Você não tem permissão para mover itens para este setor.")
                return redirect('admin_equipamentos')

            form.save()
            messages.success(request, 'Item atualizado.')
            return redirect(reverse('admin_equipamentos'))
    else:
        form = EquipamentoForm(instance=equipamento, user=request.user)
        form.fields['setor'].queryset = Setor.objects.filter(id__in=[s.id for s in setores_permitidos])
        form.fields['categoria'].queryset = Categoria.objects.filter(setor__in=setores_permitidos)

    return render(request, 'catalog/equipamento_form.html', {
        'form': form,
        'modo': 'editar',
        'equipamento': equipamento,
        'tem_categorias': tem_categorias
    })


@requer_permissao_subadmin('item')
def equipamento_excluir(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    perfil = request.user.perfil

    if not perfil.gerencia_setor(equipamento.setor, 'item'):
        messages.error(request, "Você não tem permissão para excluir itens deste setor.")
        return redirect('admin_equipamentos')

    if request.method == 'POST':
        equipamento.delete()
        messages.success(request, 'Item excluído.')
        return redirect(reverse('admin_equipamentos'))
    return render(request, 'catalog/confirmar_exclusao.html', {
        'objeto': equipamento,
        'tipo': 'item',
        'voltar_url': reverse('admin_equipamentos'),
    })


# ===============================
# CATEGORIAS
# ===============================
@requer_permissao_subadmin('item')
def categoria_criar(request):
    perfil = request.user.perfil
    if perfil.eh_admin:
        setores_permitidos = Setor.objects.all()
    else:
        setores_permitidos = [jur.setor for jur in perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]

    if not setores_permitidos:
        messages.error(request, "Você não tem permissão para gerenciar categorias.")
        return redirect('admin_equipamentos')

    if request.method == 'POST':
        form = CategoriaForm(request.POST, user=request.user)
        if form.is_valid():
            setor_escolhido = form.cleaned_data.get('setor')
            if not perfil.gerencia_setor(setor_escolhido, 'item'):
                messages.error(request, "Você não tem permissão para este setor.")
                return redirect('admin_equipamentos')

            form.save()
            messages.success(request, 'Categoria cadastrada.')
            return redirect(reverse('admin_equipamentos'))
    else:
        form = CategoriaForm(user=request.user)
        form.fields['setor'].queryset = Setor.objects.filter(id__in=[s.id for s in setores_permitidos])

    return render(request, 'catalog/categoria_form.html', {'form': form, 'modo': 'criar'})


@requer_permissao_subadmin('item')
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    perfil = request.user.perfil

    if not perfil.gerencia_setor(categoria.setor, 'item'):
        messages.error(request, "Você não tem permissão para editar categorias deste setor.")
        return redirect('admin_equipamentos')

    if perfil.eh_admin:
        setores_permitidos = Setor.objects.all()
    else:
        setores_permitidos = [jur.setor for jur in perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria, user=request.user)
        if form.is_valid():
            setor_escolhido = form.cleaned_data.get('setor')
            if not perfil.gerencia_setor(setor_escolhido, 'item'):
                messages.error(request, "Você não tem permissão para este setor.")
                return redirect('admin_equipamentos')

            form.save()
            messages.success(request, 'Categoria atualizada.')
            return redirect(reverse('admin_equipamentos'))
    else:
        form = CategoriaForm(instance=categoria, user=request.user)
        form.fields['setor'].queryset = Setor.objects.filter(id__in=[s.id for s in setores_permitidos])

    return render(request, 'catalog/categoria_form.html', {'form': form, 'modo': 'editar', 'categoria': categoria})


@requer_permissao_subadmin('item')
def categoria_excluir(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    perfil = request.user.perfil

    if not perfil.gerencia_setor(categoria.setor, 'item'):
        messages.error(request, "Você não tem permissão para excluir categorias deste setor.")
        return redirect('admin_equipamentos')

    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoria excluída.')
        except ProtectedError:
            messages.error(request, 'Não é possível excluir: esta categoria possui itens vinculados.')
        return redirect(reverse('admin_equipamentos'))
    return render(request, 'catalog/confirmar_exclusao.html', {
        'objeto': categoria,
        'tipo': 'categoria',
        'voltar_url': reverse('admin_equipamentos'),
    })


# ===============================
# LIVROS
# ===============================
@login_required
def livros(request):
    qs = Livro.objects.select_related('categoria', 'setor').annotate(total_fila=Count('fila_espera')).all()
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
    perfil = request.user.perfil
    if perfil.eh_admin:
        setores_permitidos = Setor.objects.all()
    else:
        setores_permitidos = [jur.setor for jur in perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]

    if not setores_permitidos:
        messages.error(request, "Você não tem permissão para gerenciar livros em nenhum setor.")
        return redirect('livros')
    tem_categorias = Categoria.objects.filter(setor__in=setores_permitidos).exists()
    if request.method == 'POST' and tem_categorias:
        form = LivroForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Livro cadastrado.')
            return redirect(reverse('livros'))
    else:
        form = LivroForm(user=request.user)
        # Filtra opções do form
        form.fields['setor'].queryset = Setor.objects.filter(id__in=[s.id for s in setores_permitidos])
        form.fields['categoria'].queryset = Categoria.objects.filter(setor__in=setores_permitidos)
    return render(request, 'catalog/livro_form.html', {
        'form': form,
        'modo': 'criar',
        'tem_categorias': tem_categorias
    })


@requer_permissao_subadmin('livro')
def livro_editar(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    perfil = request.user.perfil

    if not perfil.gerencia_setor(livro.setor, 'livro'):
        messages.error(request, "Você não tem permissão para editar livros deste setor.")
        return redirect('livros')

    if perfil.eh_admin:
        setores_permitidos = Setor.objects.all()
    else:
        setores_permitidos = [jur.setor for jur in perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]

    tem_categorias = Categoria.objects.filter(setor__in=setores_permitidos).exists()
    if request.method == 'POST':
        form = LivroForm(request.POST, instance=livro, user=request.user)
        if form.is_valid():
            setor_escolhido = form.cleaned_data.get('setor')
            if not perfil.gerencia_setor(setor_escolhido, 'livro'):
                messages.error(request, "Você não tem permissão para mover livros para este setor.")
                return redirect('livros')
            form.save()
            messages.success(request, 'Livro atualizado.')
            return redirect(reverse('livros'))
    else:
        form = LivroForm(instance=livro, user=request.user)
        form.fields['setor'].queryset = Setor.objects.filter(id__in=[s.id for s in setores_permitidos])
        form.fields['categoria'].queryset = Categoria.objects.filter(setor__in=setores_permitidos)
    return render(request, 'catalog/livro_form.html', {
        'form': form,
        'modo': 'editar',
        'livro': livro,
        'tem_categorias': tem_categorias
    })


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
def _notificar_admin_novo_emprestimo(request, emprestimo):
    token = secrets.token_urlsafe(32)
    emprestimo.token_acao = token
    emprestimo.save()

    aprovar_url = request.build_absolute_uri(
        reverse('aprovar_emprestimo_via_token', kwargs={'token': token})
    )
    recusar_url = request.build_absolute_uri(
        reverse('reprovar_emprestimo_via_token', kwargs={'token': token})
    )

    html_message = render_to_string('emails/email_novo_emprestimo_admin.html', {
        'emprestimo': emprestimo,
        'aprovar_url': aprovar_url,
        'recusar_url': recusar_url,
    })
    send_mail(
        'Nova solicitação de empréstimo - EngineLab',
        f'{emprestimo.usuario.get_full_name()} solicitou o empréstimo de {emprestimo.item}.',
        settings.DEFAULT_FROM_EMAIL,
        [settings.EMAIL_ADMIN_LAB],
        html_message=html_message,
    )


@login_required
def solicitar_emprestimo(request, eq_id):
    if not request.user.perfil.eh_aluno:
        messages.error(request, 'Apenas alunos podem realizar solicitações de empréstimo.')
        return redirect(reverse('equipamentos'))

    equipamento = get_object_or_404(Equipamento, pk=eq_id)
    if request.method == 'POST':
        # Verifica se já existe uma solicitação pendente idêntica para evitar duplicatas
        if Emprestimo.objects.filter(usuario=request.user, equipamento=equipamento, status=Emprestimo.STATUS_PENDENTE).exists():
            messages.warning(request, 'Você já possui uma solicitação pendente para este item.')
            return redirect(reverse('meus_emprestimos'))

        try:
            with transaction.atomic():
                emprestimo = Emprestimo(
                    usuario=request.user,
                    equipamento=equipamento,
                    data_final=request.POST.get('data_final'),
                )
                emprestimo.full_clean()
                emprestimo.save()

            _notificar_admin_novo_emprestimo(request, emprestimo)
            messages.success(request, 'Solicitação de empréstimo enviada. Aguarde a aprovação.')
            return redirect(reverse('meus_emprestimos'))
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)

    return render(request, 'catalog/confirmar_solicitacao.html', {'item': equipamento, 'tipo': 'item'})


@login_required
def solicitar_livro(request, livro_id):
    if not request.user.perfil.eh_aluno:
        messages.error(request, 'Apenas alunos podem realizar solicitações de empréstimo.')
        return redirect(reverse('livros'))

    livro = get_object_or_404(Livro, pk=livro_id)
    if request.method == 'POST':
        # Verifica duplicatas
        if Emprestimo.objects.filter(usuario=request.user, livro=livro, status=Emprestimo.STATUS_PENDENTE).exists():
            messages.warning(request, 'Você já possui uma solicitação pendente para este livro.')
            return redirect(reverse('meus_emprestimos'))

        try:
            with transaction.atomic():
                emprestimo = Emprestimo(
                    usuario=request.user,
                    livro=livro,
                    data_final=request.POST.get('data_final'),
                )
                emprestimo.full_clean()
                emprestimo.save()

            _notificar_admin_novo_emprestimo(request, emprestimo)
            messages.success(request, 'Solicitação de empréstimo enviada. Aguarde a aprovação.')
            return redirect(reverse('meus_emprestimos'))
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)

    return render(request, 'catalog/confirmar_solicitacao.html', {'item': livro, 'tipo': 'livro'})


# ===============================
# MEUS EMPRÉSTIMOS
# ===============================
@login_required
def meus_emprestimos(request):
    aba = request.GET.get('aba', 'historico')
    perfil = request.user.perfil
    hoje = date.today()

    # Queryset base para histórico e contadores
    # Se for admin/subadmin, a base é o laboratório todo (dentro da jurisdição)
    # Se for aluno, a base são apenas os seus empréstimos
    if perfil.eh_admin or perfil.eh_subadm:
        base_qs = Emprestimo.objects.select_related(
            'usuario', 'equipamento__categoria', 'equipamento__setor',
            'livro__categoria', 'livro__setor'
        )
        if not perfil.eh_admin:
            setores_permitidos = perfil.jurisdicoes.filter(pode_gerenciar_emprestimos=True).values_list('setor', flat=True)
            base_qs = base_qs.filter(
                Q(equipamento__setor_id__in=setores_permitidos) | Q(livro__setor_id__in=setores_permitidos)
            )
    else:
        base_qs = Emprestimo.objects.filter(usuario=request.user).select_related(
            'equipamento__categoria', 'equipamento__setor',
            'livro__categoria', 'livro__setor'
        )

    # Filtros de busca (aplicados ao histórico e renovação se for admin)
    search_query = request.GET.get('q', '')
    setor_selecionado = request.GET.get('setor')
    status_selecionado = request.GET.get('status')

    # Queryset para a aba HISTÓRICO
    emprestimos_qs = base_qs
    if aba == 'historico':
        if search_query:
            emprestimos_qs = emprestimos_qs.filter(
                Q(usuario__first_name__icontains=search_query) |
                Q(usuario__username__icontains=search_query) |
                Q(equipamento__nome__icontains=search_query) |
                Q(livro__titulo__icontains=search_query)
            )
        if setor_selecionado:
            emprestimos_qs = emprestimos_qs.filter(
                Q(equipamento__setor_id=setor_selecionado) | Q(livro__setor_id=setor_selecionado)
            )
        if status_selecionado:
            emprestimos_qs = emprestimos_qs.filter(status=status_selecionado)

    # Contadores SEMPRE baseados no perfil (todos os do lab para admin, só os meus para aluno)
    contadores = {status: base_qs.filter(status=status).count() for status, _ in Emprestimo.STATUS_CHOICES}

    # Aba RENOVAÇÃO
    if aba == 'renovacao':
        emprestimos_ativos = base_qs.filter(status=Emprestimo.STATUS_ATIVO)
        if search_query:
            emprestimos_ativos = emprestimos_ativos.filter(
                Q(usuario__first_name__icontains=search_query) |
                Q(equipamento__nome__icontains=search_query) |
                Q(livro__titulo__icontains=search_query)
            )
        if setor_selecionado:
            emprestimos_ativos = emprestimos_ativos.filter(
                Q(equipamento__setor_id=setor_selecionado) | Q(livro__setor_id=setor_selecionado)
            )
    else:
        # Fallback para não quebrar o template se não estiver na aba renovação
        emprestimos_ativos = base_qs.filter(status=Emprestimo.STATUS_ATIVO)

    # Lógica de "Pode Renovar"
    for emp in emprestimos_ativos:
        atrasado = emp.data_final < hoje
        limite_atingido = emp.vezes_renovado >= 5
        prazo_renovacao = emp.data_final - timedelta(days=2)
        muito_cedo = hoje < prazo_renovacao

        if perfil.eh_admin or perfil.eh_subadm:
            emp.pode_renovar = True
            emp.motivo_bloqueio = ""
        else:
            emp.pode_renovar = not (atrasado or limite_atingido or muito_cedo)
            emp.motivo_bloqueio = ""
            if atrasado: emp.motivo_bloqueio = "Item atrasado"
            elif limite_atingido: emp.motivo_bloqueio = "Limite de renovações atingido"
            elif muito_cedo: emp.motivo_bloqueio = f"Disponível em {prazo_renovacao.strftime('%d/%m/%Y')}"

    # Aba RESERVA
    itens_reserva = []
    if aba == 'reserva':
        eqs = Equipamento.objects.select_related('categoria', 'setor').all()
        livs = Livro.objects.select_related('categoria', 'setor').all()
        if search_query:
            eqs = eqs.filter(Q(nome__icontains=search_query) | Q(categoria__nome__icontains=search_query))
            livs = livs.filter(Q(titulo__icontains=search_query) | Q(categoria__nome__icontains=search_query))
        if setor_selecionado:
            eqs = eqs.filter(setor_id=setor_selecionado); livs = livs.filter(setor_id=setor_selecionado)
        for e in eqs: itens_reserva.append({'obj': e, 'tipo': 'item', 'nome': e.nome, 'setor': e.setor.nome, 'cat': e.categoria.nome, 'status': e.status})
        for l in livs: itens_reserva.append({'obj': l, 'tipo': 'livro', 'nome': l.titulo, 'setor': l.setor.nome, 'cat': l.categoria.nome, 'status': l.status})

    # Aba DÉBITO
    debitos = []
    if aba == 'debito':
        debitos_qs = base_qs.filter(status=Emprestimo.STATUS_ATIVO, data_final__lt=hoje)
        for d in debitos_qs:
            d.dias_atraso = (hoje - d.data_final).days
        debitos = debitos_qs

    return render(request, 'catalog/meus_emprestimos.html', {
        'emprestimos': emprestimos_qs,
        'emprestimos_ativos': emprestimos_ativos,
        'itens_reserva': itens_reserva,
        'debitos': debitos,
        'contadores': contadores,
        'status_choices': Emprestimo.STATUS_CHOICES,
        'status_selecionado': status_selecionado,
        'aba_ativa': aba,
        'search_query': search_query,
        'setor_selecionado': setor_selecionado,
        'setores': Setor.objects.all(),
        'hoje': hoje,
    })

    return render(request, 'catalog/meus_emprestimos.html', {
        'emprestimos': emprestimos_qs,
        'emprestimos_ativos': emprestimos_ativos,
        'itens_reserva': itens_reserva,
        'debitos': debitos,
        'contadores': contadores,
        'status_choices': Emprestimo.STATUS_CHOICES,
        'status_selecionado': status_selecionado,
        'aba_ativa': aba,
        'search_query': search_query,
        'setor_selecionado': setor_selecionado,
        'setores': Setor.objects.all(),
        'hoje': hoje,
    })


@login_required
def renovar_emprestimo(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk, status=Emprestimo.STATUS_ATIVO)
    perfil = request.user.perfil

    # Se não for o dono nem admin/subadmin do setor, nega
    if emprestimo.usuario != request.user:
        if not perfil.gerencia_setor(emprestimo.item.setor, 'emprestimo'):
             messages.error(request, "Você não tem permissão para renovar este empréstimo.")
             return redirect(reverse('meus_emprestimos') + '?aba=renovacao')

    hoje = date.today()
    atrasado = emprestimo.data_final < hoje
    limite_atingido = emprestimo.vezes_renovado >= 5

    pode_prosseguir = True
    if not (perfil.eh_admin or perfil.eh_subadm):
        if atrasado or limite_atingido:
            pode_prosseguir = False
            msg = "Não foi possível renovar este item."
            if atrasado: msg = "Não é possível renovar um item atrasado."
            elif limite_atingido: msg = "Limite de renovações atingido (máximo 5)."
            messages.error(request, msg)

    if pode_prosseguir:
        # Renova por mais 7 dias
        emprestimo.data_final += timedelta(days=7)
        emprestimo.vezes_renovado += 1
        emprestimo.save()
        messages.success(request, f"Item renovado com sucesso! Nova data de devolução: {emprestimo.data_final.strftime('%d/%m/%Y')}")

    return redirect(reverse('meus_emprestimos') + '?aba=renovacao')


# ===============================
# ADMIN — EMPRÉSTIMOS
# ===============================
@requer_subadm
def admin_emprestimos(request):
    perfil = request.user.perfil
    qs = Emprestimo.objects.select_related('usuario', 'equipamento', 'livro', 'equipamento__setor', 'livro__setor').all()

    if perfil.eh_admin:
        setores_permitidos = Setor.objects.all()
    else:
        # Pega setores onde ele pode gerenciar empréstimos
        setores_permitidos = [jur.setor for jur in perfil.jurisdicoes.filter(pode_gerenciar_emprestimos=True)]
        qs = qs.filter(
            Q(equipamento__setor__in=setores_permitidos) | Q(livro__setor__in=setores_permitidos)
        )

    status = request.GET.get('status')
    search_query = request.GET.get('q', '')
    setor_id = request.GET.get('setor')
    data_de = request.GET.get('data_de')
    data_ate = request.GET.get('data_ate')

    if status:
        qs = qs.filter(status=status)
    if setor_id:
        qs = qs.filter(Q(equipamento__setor_id=setor_id) | Q(livro__setor_id=setor_id))
    if data_de:
        qs = qs.filter(data_inicio__gte=data_de)
    if data_ate:
        qs = qs.filter(data_inicio__lte=data_ate)
    if search_query:
        qs = qs.filter(
            Q(usuario__first_name__icontains=search_query) |
            Q(usuario__last_name__icontains=search_query) |
            Q(usuario__email__icontains=search_query) |
            Q(equipamento__nome__icontains=search_query) |
            Q(equipamento__identificador__icontains=search_query) |
            Q(livro__titulo__icontains=search_query) |
            Q(livro__isbn__icontains=search_query)
        )

    return render(request, 'catalog/admin_emprestimos.html', {
        'emprestimos': qs,
        'status_choices': Emprestimo.STATUS_CHOICES,
        'setores': setores_permitidos,
        'status_selecionado': status,
        'search_query': search_query,
        'setor_selecionado': setor_id,
        'data_de': data_de,
        'data_ate': data_ate,
    })


@requer_subadm
def aprovar_emprestimo(request, pk):
    perfil = request.user.perfil
    emprestimo = Emprestimo.objects.filter(pk=pk).first()
    if not emprestimo:
        messages.error(request, 'Solicitação não encontrada.')
        return redirect('admin_emprestimos')

    if emprestimo.status != Emprestimo.STATUS_PENDENTE:
        messages.info(request, f'Esta solicitação já foi processada (Status: {emprestimo.get_status_display()}).')
        return redirect('admin_emprestimos')

    # Segurança: Verifica se o item pertence a um setor onde ele pode gerenciar EMPRÉSTIMOS
    setor_item = emprestimo.item.setor
    if not perfil.gerencia_setor(setor_item, 'emprestimo'):
        messages.error(request, 'Você não tem permissão para aprovar empréstimos deste setor.')
        return redirect('admin_emprestimos')

    if request.method == 'POST':
        with transaction.atomic():
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
        messages.success(request, f'Empréstimo de {item} para {emprestimo.usuario.first_name} aprovado.')
    return redirect(reverse('admin_emprestimos'))


@requer_subadm
def reprovar_emprestimo(request, pk):
    perfil = request.user.perfil
    emprestimo = Emprestimo.objects.filter(pk=pk).first()
    if not emprestimo:
        messages.error(request, 'Solicitação não encontrada.')
        return redirect('admin_emprestimos')

    if emprestimo.status != Emprestimo.STATUS_PENDENTE:
        messages.info(request, f'Esta solicitação já foi processada (Status: {emprestimo.get_status_display()}).')
        return redirect('admin_emprestimos')

    # Segurança: Verifica se o item pertence a um setor onde ele pode gerenciar EMPRÉSTIMOS
    setor_item = emprestimo.item.setor
    if not perfil.gerencia_setor(setor_item, 'emprestimo'):
        messages.error(request, 'Você não tem permissão para reprovar empréstimos deste setor.')
        return redirect('admin_emprestimos')

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
    perfil = request.user.perfil
    emprestimo = get_object_or_404(Emprestimo, pk=pk, status=Emprestimo.STATUS_ATIVO)

    # Segurança: Verifica permissão de empréstimo
    setor_item = emprestimo.item.setor
    if not perfil.gerencia_setor(setor_item, 'emprestimo'):
        messages.error(request, 'Você não tem permissão para finalizar empréstimos deste setor.')
        return redirect('admin_emprestimos')

    if request.method == 'POST':
        emprestimo.status = Emprestimo.STATUS_FINALIZADO
        emprestimo.data_devolucao = date.today()
        emprestimo.save()

        item = emprestimo.item
        item.status = item.STATUS_DISPONIVEL
        item.save()

        msg = f'Item {item} devolvido com sucesso. O item agora está disponível.'
        messages.success(request, msg)
    return redirect(reverse('admin_emprestimos'))


def aprovar_emprestimo_via_token(request, token):
    emprestimo = Emprestimo.objects.filter(token_acao=token).first()
    if not emprestimo:
        return render(request, 'registration/acao_ja_realizada.html', {'perfil': None})

    if emprestimo.status != Emprestimo.STATUS_PENDENTE:
        return render(request, 'registration/acao_ja_realizada.html', {
            'perfil': emprestimo.usuario.perfil,
            'mensagem_personalizada': f'Esta solicitação do item "{emprestimo.item}" já foi processada anteriormente. Status atual: {emprestimo.get_status_display()}.'
        })

    emprestimo.status = Emprestimo.STATUS_ATIVO
    emprestimo.token_acao = None
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

    return render(request, 'registration/resultado_aprovacao.html', {
        'perfil': emprestimo.usuario.perfil,
        'acao': 'aprovado',
        'mensagem_personalizada': f'O empréstimo do item "{item}" para {emprestimo.usuario.get_full_name()} foi APROVADO com sucesso.'
    })


def reprovar_emprestimo_via_token(request, token):
    emprestimo = Emprestimo.objects.filter(token_acao=token).first()
    if not emprestimo:
        return render(request, 'registration/acao_ja_realizada.html', {'perfil': None})

    if emprestimo.status != Emprestimo.STATUS_PENDENTE:
        return render(request, 'registration/acao_ja_realizada.html', {
            'perfil': emprestimo.usuario.perfil,
            'mensagem_personalizada': f'Esta solicitação do item "{emprestimo.item}" já foi processada anteriormente. Status atual: {emprestimo.get_status_display()}.'
        })

    emprestimo.status = Emprestimo.STATUS_REJEITADO
    emprestimo.token_acao = None
    emprestimo.save()

    html_message = render_to_string('emails/email_emprestimo_recusado.html', {'emprestimo': emprestimo})
    send_mail(
        'Empréstimo não aprovado - EngineLab',
        f'Seu pedido de empréstimo de {emprestimo.item} não foi aprovado.',
        settings.DEFAULT_FROM_EMAIL,
        [emprestimo.usuario.email],
        html_message=html_message,
    )

    return render(request, 'registration/resultado_aprovacao.html', {
        'perfil': emprestimo.usuario.perfil,
        'acao': 'recusado',
        'mensagem_personalizada': f'O empréstimo do item "{emprestimo.item}" para {emprestimo.usuario.get_full_name()} foi RECUSADO.'
    })


@requer_subadm
def emprestimo_direto(request, tipo, pk):
    perfil = request.user.perfil
    if tipo == 'item':
        obj = get_object_or_404(Equipamento, pk=pk)
    else:
        obj = get_object_or_404(Livro, pk=pk)

    if not perfil.gerencia_setor(obj.setor, 'emprestimo'):
        messages.error(request, "Você não tem permissão para realizar empréstimos neste setor.")
        return redirect('itens_setor', setor_id=obj.setor.pk)

    if obj.status == 'emprestado':
        messages.error(request, "Este item já está emprestado.")
        return redirect('itens_setor', setor_id=obj.setor.pk)

    from .forms import EmprestimoDiretoForm

    # Prepara a instância com o item para passar na validação do clean()
    instancia = Emprestimo()
    if tipo == 'item':
        instancia.equipamento = obj
    else:
        instancia.livro = obj

    if request.method == 'POST':
        form = EmprestimoDiretoForm(request.POST, instance=instancia)
        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.status = Emprestimo.STATUS_ATIVO
            emprestimo.save()

            obj.status = 'emprestado'
            obj.save()

            messages.success(request, f"Empréstimo de {obj} para {emprestimo.usuario.get_full_name() or emprestimo.usuario.username} realizado com sucesso.")
            return redirect('itens_setor', setor_id=obj.setor.pk)
    else:
        form = EmprestimoDiretoForm(instance=instancia)

    return render(request, 'catalog/confirmar_solicitacao.html', {
        'item': obj,
        'tipo': tipo,
        'form': form,
        'modo_direto': True
    })


def renovar_emprestimo_via_token(request, token):
    from datetime import timedelta
    emprestimo = get_object_or_404(Emprestimo, token_renovacao=token, status=Emprestimo.STATUS_ATIVO)

    # Renova por mais 30 dias
    emprestimo.data_final += timedelta(days=30)
    emprestimo.token_renovacao = None # Invalida o token após uso
    emprestimo.save()

    return render(request, 'registration/resultado_aprovacao.html', {
        'perfil': emprestimo.usuario.perfil,
        'acao': 'aprovado',
        'mensagem_personalizada': f'Seu empréstimo do item "{emprestimo.item}" foi renovado com sucesso até {emprestimo.data_final.strftime("%d/%m/%Y")}.'
    })
