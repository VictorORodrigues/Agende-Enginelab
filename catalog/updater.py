from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

def start():
    scheduler = BackgroundScheduler()
    # Adiciona a tarefa para rodar o comando que criamos anteriormente
    # 'interval' de 24 horas (pode ser 'cron' para um horário fixo, ex: todo dia às 08h)
    scheduler.add_job(call_notificar_atrasos, 'interval', hours=24, next_run_time=datetime.now())
    scheduler.start()

def call_notificar_atrasos():
    try:
        # Chama o comando que você já tem: python manage.py notificar_atrasos
        call_command('notificar_atrasos')
    except Exception as e:
        print(f"Erro ao rodar tarefa automática: {e}")
