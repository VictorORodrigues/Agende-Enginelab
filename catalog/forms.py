from django import forms

from .models import Categoria, Equipamento, Livro, Emprestimo


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'setor', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'maxlength': '50', 'placeholder': 'Ex: Eletrônicos'}),
            'descricao': forms.Textarea(attrs={'maxlength': '300', 'rows': 3, 'placeholder': 'Breve descrição da categoria...'}),
        }
        labels = {
            'nome': 'Nome',
            'setor': 'Setor',
            'descricao': 'Descrição',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from account.models import Setor
        if user and user.perfil.eh_subadm and not user.perfil.eh_admin:
            setores_permitidos = [jur.setor for jur in user.perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]
            self.fields['setor'].queryset = Setor.objects.filter(id__in=[s.id for s in setores_permitidos]).order_by('nome')
        else:
            self.fields['setor'].queryset = Setor.objects.order_by('nome')


class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = ['nome', 'setor', 'categoria', 'identificador', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'maxlength': '100'}),
            'identificador': forms.TextInput(attrs={'maxlength': '50'}),
            'descricao': forms.Textarea(attrs={'maxlength': '500', 'rows': 3}),
        }
        labels = {
            'nome': 'Nome do Item',
            'identificador': 'Identificador (ID)',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from account.models import Setor

        if user and user.perfil.eh_subadm and not user.perfil.eh_admin:
            setores_permitidos = [jur.setor for jur in user.perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]
            setor_ids = [s.id for s in setores_permitidos]

            self.fields['setor'].queryset = Setor.objects.filter(id__in=setor_ids).order_by('nome')
            self.fields['categoria'].queryset = Categoria.objects.filter(setor_id__in=setor_ids).order_by('nome')
        else:
            self.fields['setor'].queryset = Setor.objects.order_by('nome')
            self.fields['categoria'].queryset = Categoria.objects.order_by('nome')


class LivroForm(forms.ModelForm):
    class Meta:
        model = Livro
        fields = ['titulo', 'autor', 'setor', 'categoria', 'isbn', 'exemplares']
        widgets = {
            'titulo': forms.TextInput(attrs={'maxlength': '150'}),
            'autor': forms.TextInput(attrs={'maxlength': '150'}),
            'isbn': forms.TextInput(attrs={'maxlength': '20'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from account.models import Setor

        if user and user.perfil.eh_subadm and not user.perfil.eh_admin:
            setores_permitidos = [jur.setor for jur in user.perfil.jurisdicoes.filter(pode_gerenciar_itens=True)]
            setor_ids = [s.id for s in setores_permitidos]

            self.fields['setor'].queryset = Setor.objects.filter(id__in=setor_ids).order_by('nome')
            self.fields['categoria'].queryset = Categoria.objects.filter(setor_id__in=setor_ids).order_by('nome')
        else:
            self.fields['setor'].queryset = Setor.objects.order_by('nome')
            self.fields['categoria'].queryset = Categoria.objects.order_by('nome')

    def clean_isbn(self):
        isbn = (self.cleaned_data.get('isbn') or '').strip()
        return isbn or None


class EmprestimoDiretoForm(forms.ModelForm):
    class Meta:
        model = Emprestimo
        fields = ['usuario', 'data_final']
        widgets = {
            'data_final': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'usuario': 'Aluno / Usuário',
            'data_final': 'Data de Devolução',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        # Apenas usuários ativos e preferencialmente alunos (embora possa emprestar para subadmin se necessário)
        self.fields['usuario'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        # Melhora a exibição do usuário no select
        self.fields['usuario'].label_from_instance = lambda obj: f"{obj.get_full_name() or obj.username} ({obj.email})"
