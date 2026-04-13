from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Equipamento, Emprestimo, Perfil, FilaEspera, Categoria

admin.site.register(Equipamento)
admin.site.register(Emprestimo)
admin.site.register(Categoria)
admin.site.register(Perfil)
admin.site.register(FilaEspera)