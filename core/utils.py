from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# --- FUNÇÃO 1: PARA O ADMINISTRADOR (SOLICITAÇÃO) ---
def enviar_email_solicitacao_adm(emprestimo):
    base_url = "http://127.0.0.1:8000" # Em produção, use seu domínio
    subject = f'Nova Solicitação: {emprestimo.equipamento.nome}'
    
    html_content = f"""
    <h2>Olá, Administrador!</h2>
    <p>O aluno <strong>{emprestimo.usuario.username}</strong> solicitou o equipamento <strong>{emprestimo.equipamento.nome}</strong>.</p>
    <p>Data de devolução prevista: {emprestimo.data_final}</p>
    <br>
    <a href="{base_url}/emprestimo/aprovar/{emprestimo.id}/" style="background-color: #198754; color: white; padding: 10px; text-decoration: none; border-radius: 5px;">APROVAR</a>
    <a href="{base_url}/emprestimo/reprovar/{emprestimo.id}/" style="background-color: #dc3545; color: white; padding: 10px; text-decoration: none; border-radius: 5px;">REPROVAR</a>
    """
    
    msg = EmailMultiAlternatives(subject, strip_tags(html_content), settings.EMAIL_HOST_USER, [settings.EMAIL_ADMIN_LAB])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

# --- FUNÇÃO 2: PARA O ALUNO (RESULTADO) ---
def enviar_email_resultado_aluno(emprestimo, status):
    subject = f'Resultado da sua solicitação: {emprestimo.equipamento.nome}'
    
    # Define a mensagem baseada no que o professor decidiu
    status_msg = "APROVADA" if status == 'ativo' else "REPROVADA"
    cor_status = "#198754" if status == 'ativo' else "#dc3545"

    html_content = f"""
    <div style="font-family: sans-serif;">
        <h2>Olá, {emprestimo.usuario.username}!</h2>
        <p>Sua solicitação para o equipamento <strong>{emprestimo.equipamento.nome}</strong> foi <strong style="color: {cor_status};">{status_msg}</strong>.</p>
        <p>Caso tenha dúvidas, procure o laboratório EngineLab UFC.</p>
    </div>
    """
    
    msg = EmailMultiAlternatives(subject, strip_tags(html_content), settings.EMAIL_HOST_USER, [emprestimo.usuario.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()