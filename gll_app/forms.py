from django import forms
from .models import *
from datetime import date

class GalloForm(forms.ModelForm):
    class Meta:
        model = Gallo
        exclude = ['placaPadre', 'placaMadre']
        widgets = {
            'nroPlaca': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'tipoGallo': forms.Select(attrs={'class': 'form-select'}),
            #'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nombre_img': forms.FileInput(attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control'}),
            'nroPlacaAnterior': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombreDuenoAnterior': forms.Select(attrs={'class': 'form-control'}),
            'estadoDeSalud': forms.Select(attrs={'class': 'form-select'}),
            'fechaMuerte': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                },
                format='%Y-%m-%d'
            ),
            'color': forms.Select(attrs={'class': 'form-control'}),
        }

    fechaNac = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            },
            format='%Y-%m-%d'
        ),
        label="Fecha de Nacimiento"
    )

    nombreDuenoAnterior = forms.ModelChoiceField(
        queryset=DuenoAnterior.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = date.today().strftime('%Y-%m-%d')
        self.fields['fechaNac'].widget.attrs['max'] = hoy

class EncuentroForm(forms.ModelForm):
    class Meta:
        model = Encuentro
        fields = [
            'fechaYHora', 'galpon1', 'galpon2', 'video',
            'pactada', 'pago_juez', 'apuesta_general',
            'premio_mayor', 'porcentaje_premio_mayor', 'apuesta_por_fuera',
            'resultado', 'condicionGallo', 'imagen_evento',
        ]
        widgets = {
            'fechaYHora': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'video': forms.ClearableFileInput(attrs={'accept': 'video/*'}),
            'resultado': forms.Select(attrs={'class': 'form-select'}),
            #'duenoEvento': forms.Select(attrs={'class': 'form-select'}),
            'imagen_evento': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super(EncuentroForm, self).__init__(*args, **kwargs)
        self.fields['porcentaje_premio_mayor'].initial = 10
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
        self.fields['video'].required = False
        self.fields['imagen_evento'].required = False
        self.fields['pago_juez'].required = False
        self.fields['premio_mayor'].required = False
        self.fields['porcentaje_premio_mayor'].required = False

    def clean(self):
        cleaned_data = super().clean()
        premio_mayor = cleaned_data.get('premio_mayor')
        porcentaje_premio_mayor = cleaned_data.get('porcentaje_premio_mayor')
        if premio_mayor is None:
            cleaned_data['premio_mayor'] = 0
        if porcentaje_premio_mayor is None:
            cleaned_data['porcentaje_premio_mayor'] = 0

        return cleaned_data
        
        
class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del color'}),
        }

class EstadoForm(forms.ModelForm):
    class Meta:
        model = Estado
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del estado'}),
        }

class GalponForm(forms.ModelForm):
    class Meta:
        model = Galpon
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del galpón'}),
        }
"""
class DuenoForm(forms.ModelForm):
    class Meta:
        model = Dueno
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del dueño'}),
        }
"""
class DuenoAnteriorForm(forms.ModelForm):
    class Meta:
        model = DuenoAnterior
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del dueño anterior'}),
        }