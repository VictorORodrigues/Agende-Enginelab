from django import forms

from .models import Categoria, Equipamento, Livro


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao']


class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = ['nome', 'categoria', 'status', 'identificador', 'descricao']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.order_by('nome')


class LivroForm(forms.ModelForm):
    class Meta:
        model = Livro
        fields = ['titulo', 'autor', 'categoria', 'isbn', 'status', 'exemplares']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.order_by('nome')

    def clean_isbn(self):
        isbn = (self.cleaned_data.get('isbn') or '').strip()
        return isbn or None
