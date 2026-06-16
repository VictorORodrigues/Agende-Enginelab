from datetime import date

from django import forms

from .models import Agendamento


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['setor', 'data', 'hora_inicio', 'hora_fim', 'motivo']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_data(self):
        data = self.cleaned_data['data']
        if data < date.today():
            raise forms.ValidationError('Não é possível agendar em uma data passada.')
        return data

    def clean(self):
        cleaned_data = super().clean()
        setor = cleaned_data.get('setor')
        data = cleaned_data.get('data')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fim = cleaned_data.get('hora_fim')

        if hora_inicio and hora_fim and hora_fim <= hora_inicio:
            raise forms.ValidationError('O horário final deve ser depois do horário inicial.')

        if setor and data and hora_inicio and hora_fim:
            conflito = Agendamento.objects.filter(
                setor=setor,
                data=data,
                status__in=[Agendamento.STATUS_PENDENTE, Agendamento.STATUS_APROVADO],
                hora_inicio__lt=hora_fim,
                hora_fim__gt=hora_inicio,
            )
            if self.instance.pk:
                conflito = conflito.exclude(pk=self.instance.pk)
            if conflito.exists():
                raise forms.ValidationError(
                    'Já existe um agendamento nesse setor que conflita com esse horário.'
                )

        return cleaned_data
