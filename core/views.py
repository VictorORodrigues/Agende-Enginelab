from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistroForm
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.decorators import login_required
from .models import Equipamento, Emprestimo, FilaEspera
from django.contrib.auth.tokens import default_token_generator
from django.contrib.admin.views.decorators import staff_member_required
from .utils import enviar_email_solicitacao_adm, enviar_email_resultado_aluno
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.contrib.auth import login
from decouple import config

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Conta inativa até confirmar e-mail
            user.set_password(form.cleaned_data['senha'])
            user.save()

            # Gerar dados para o link único
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            link = f"http://{domain}/accounts/ativar/{uid}/{token}/"

            # Configuração do E-mail HTML
            assunto = 'Ative sua conta no EngineLab'
            mensagem_txt = f"Olá {user.first_name}, ative sua conta aqui: {link}"
            html_content = f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #007bff; text-align: center;">Bem-vindo ao Agende EngineLab!</h2>
                    <p>Olá <strong>{user.first_name}</strong>,</p>
                    <p>Para concluir seu cadastro, clique no botão abaixo:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{link}" style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                            CONFIRMAR E-MAIL
                        </a>
                    </div>
                    <p style="font-size: 0.8em; color: #666;">Se o botão não funcionar: {link}</p>
                </div>
            """

            send_mail(
                assunto,
                mensagem_txt,
                config('EMAIL_HOST_USER'),
                [user.email],
                html_message=html_content
            )

            return render(request, 'registration/confirmacao_enviada.html')
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {'form': form})

# --- VIEW DE ATIVAÇÃO ---
def ativar_conta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        
        # LOGA O USUÁRIO AUTOMATICAMENTE
        login(request, user) 
        
        messages.success(request, f"Bem-vindo, {user.first_name}! Sua conta foi ativada com sucesso.")
        return redirect('index') # Redireciona direto para a página inicial logado
    else:
        return render(request, 'registration/link_invalido.html')
    

# --- PAINEL PRINCIPAL ---
@login_required
def index(request):
    return render(request, 'core/index.html')

# --- ALUNO SOLICITA EMPRÉSTIMO ---
@login_required
def solicitar_emprestimo(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)
    
    if request.method == 'POST':
        data_entrega = request.POST.get('data_final')
        
        novo_emprestimo = Emprestimo.objects.create(
            usuario=request.user,
            equipamento=equipamento,
            data_final=data_entrega,
            status='pendente'
        )
        
        try:
            enviar_email_solicitacao_adm(novo_emprestimo)
            messages.success(request, "Solicitação enviada ao administrador!")
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            messages.warning(request, "Solicitação salva, mas houve um erro ao notificar o administrador.")
        
        return redirect('index')

    return render(request, 'core/confirmar_solicitacao.html', {'equipamento': equipamento})

# --- ADMINISTRADOR APROVA (VIA E-MAIL OU LINK) ---
@staff_member_required
def aprovar_emprestimo(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    
    # Atualiza o Empréstimo
    emprestimo.status = 'ativo'
    emprestimo.save()
    
    # Atualiza o Equipamento para não aparecer como disponível
    equipamento = emprestimo.equipamento
    equipamento.status = 'emprestado'
    equipamento.save()
    
    # Notifica o aluno da aprovação
    try:
        enviar_email_resultado_aluno(emprestimo, 'ativo')
    except Exception as e:
        print(f"Erro ao notificar aluno: {e}")
    
    return render(request, 'core/resultado_acao.html', {'status': 'Aprovado', 'emprestimo': emprestimo})

# --- ADMINISTRADOR REPROVA ---
@staff_member_required
def reprovar_emprestimo(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    emprestimo.status = 'rejeitado'
    emprestimo.save()
    
    enviar_email_resultado_aluno(emprestimo, 'rejeitado')
    
    return render(request, 'core/resultado_acao.html', {'status': 'Reprovado', 'emprestimo': emprestimo})