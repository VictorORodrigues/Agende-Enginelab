from .models import Setor

def setores_processor(request):
    return {
        'todos_setores': Setor.objects.all().order_by('nome')
    }
