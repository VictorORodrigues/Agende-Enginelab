from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from catalog.models import Emprestimo
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Notifica por e-mail os usuários com empréstimos atrasados'

    def handle(self, *args, **options):
        hoje = timezone.now().date()
        atrasados = Emprestimo.objects.filter(
            status=Emprestimo.STATUS_ATIVO,
            data_final__lt=hoje
        ).select_related('usuario')

        self.stdout.write(f'Iniciando verificação de atrasos... Encontrados: {atrasados.count()}')

        count_sucesso = 0
        for emp in atrasados:
            try:
                html_message = render_to_string('emails/email_atraso_notificacao.html', {
                    'emprestimo': emp,
                })

                send_mail(
                    subject=f'ATENÇÃO: Item em atraso - {emp.item}',
                    message=f'Olá {emp.usuario.first_name}, o item {emp.item} está atrasado.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[emp.usuario.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                count_sucesso += 1
                self.stdout.write(self.style.SUCCESS(f'Notificação enviada para: {emp.usuario.email} (Item: {emp.item})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao enviar para {emp.usuario.email}: {str(e)}'))
                logger.exception(f'Falha ao enviar notificação de atraso para {emp.usuario.email}')

        self.stdout.write(self.style.SUCCESS(f'Processamento concluído. {count_sucesso} e-mails enviados.'))
