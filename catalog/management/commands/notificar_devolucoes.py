import secrets
from datetime import date
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from catalog.models import Emprestimo

class Command(BaseCommand):
    help = 'Envia notificações por e-mail para usuários e admin sobre itens que vencem hoje'

    def handle(self, *args, **options):
        hoje = date.today()
        # Busca empréstimos ativos que vencem hoje
        emprestimos_vencendo = Emprestimo.objects.filter(
            data_final=hoje,
            status=Emprestimo.STATUS_ATIVO
        ).select_related('usuario', 'equipamento', 'livro')

        total = emprestimos_vencendo.count()
        self.stdout.write(f'Encontrados {total} empréstimos vencendo hoje.')

        if total == 0:
            self.stdout.write('Nenhuma devolução para hoje.')
            return

        # 1. Notifica os Usuários Individualmente
        for emprestimo in emprestimos_vencendo:
            # Gera um token para renovação
            token = secrets.token_urlsafe(32)
            emprestimo.token_renovacao = token
            emprestimo.save()

            dominio = 'http://127.0.0.1:8000' # Ajustar em produção
            renovar_url = f"{dominio}{reverse('renovar_emprestimo_via_token', kwargs={'token': token})}"

            html_user = render_to_string('emails/email_vencimento_emprestimo.html', {
                'emprestimo': emprestimo,
                'renovar_url': renovar_url,
                'header_cor': '#b45309',
            })

            try:
                send_mail(
                    f'EngineLab: Lembrete de devolução - {emprestimo.item}',
                    f'Olá {emprestimo.usuario.first_name}, hoje é o dia de devolver o item {emprestimo.item}.',
                    settings.DEFAULT_FROM_EMAIL,
                    [emprestimo.usuario.email],
                    html_message=html_user,
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f'Notificação enviada para usuário: {emprestimo.usuario.email}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao enviar para usuário {emprestimo.usuario.email}: {str(e)}'))

        # 2. Notifica o Admin com a lista completa do dia
        html_admin = render_to_string('emails/email_vencimento_admin.html', {
            'emprestimos': emprestimos_vencendo,
            'data': hoje.strftime('%d/%m/%Y'),
            'header_cor': '#b45309',
        })

        try:
            send_mail(
                f'EngineLab: Alerta de Devoluções do Dia - {hoje.strftime("%d/%m/%Y")}',
                f'Existem {total} devoluções previstas para hoje.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_ADMIN_LAB],
                html_message=html_admin,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('E-mail de resumo enviado ao administrador.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao enviar e-mail para o administrador: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Processo de notificações concluído.'))
