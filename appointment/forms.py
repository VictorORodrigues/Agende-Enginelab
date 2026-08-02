from django import forms
from .models import Agendamento
from account.models import Setor
from datetime import date

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['setor', 'data', 'data_final', 'dia_inteiro', 'hora_inicio', 'hora_fim']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'data_final': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_data(self):
        data = self.cleaned_data.get('data')
        if data and data < date.today():
            raise forms.ValidationError("A data não pode ser no passado.")
        return data

    def clean(self):
        cleaned_data = super().clean()
        dia_inteiro = cleaned_data.get('dia_inteiro')
        inicio = cleaned_data.get('hora_inicio')
        fim = cleaned_data.get('hora_fim')
        data_inicio = cleaned_data.get('data')
        data_final = cleaned_data.get('data_final')

        from datetime import timedelta

        if data_inicio and data_final:
            if data_final < data_inicio:
                self.add_error('data_final', "A data de devolução não pode ser anterior à data de início.")

            if data_final > data_inicio + timedelta(days=30):
                self.add_error('data_final', "O período de agendamento não pode exceder 30 dias.")

        if not dia_inteiro:
            if not inicio:
                self.add_error('hora_inicio', "Este campo é obrigatório se não for o dia inteiro.")
            if not fim:
                self.add_error('hora_fim', "Este campo é obrigatório se não for o dia inteiro.")

            if inicio and fim and inicio >= fim:
                raise forms.ValidationError("A hora de início deve ser anterior à hora de fim.")
        else:
            # Se for dia inteiro, limpamos os horários caso tenham sido preenchidos
            cleaned_data['hora_inicio'] = None
            cleaned_data['hora_fim'] = None

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se o campo setor estiver desabilitado via widget, ele não é enviado no POST.
        # Vamos garantir que ele não seja obrigatório no form para não travar a validação,
        # e o valor será tratado na view.
        if 'setor' in self.fields:
            self.fields['setor'].required = False
