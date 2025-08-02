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

    nombre_img = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

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
    nroPlaca = forms.ModelChoiceField(
        queryset=PlacaCheck.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="Número de Placa"
    )
    nroPlacaAnterior = forms.ModelChoiceField(
        queryset=PlacaCheck.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="Número de Placa Anterior"
    )
    peso = forms.ModelChoiceField(
        queryset=PesosCheck.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="Peso (libras)"
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = date.today().strftime('%Y-%m-%d')
        self.fields['fechaNac'].widget.attrs['max'] = hoy
        self.fields['fechaMuerte'].required = False
        if self.instance and self.instance.pk:
            self.fields['nombre_img'].required = False

class EncuentroForm(forms.ModelForm):
    
    video = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'video/*'})
    )
    imagen_evento = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'})
    )

    class Meta:
        model = Encuentro
        fields = [
            'fechaYHora', 'galpon1', 'galpon2', 'video',
            'pactada', 'pago_juez', 'apuesta_general',
            'premio_mayor', 'porcentaje_premio_mayor', 'apuesta_por_fuera',
            'resultado', 'condicionGallo', 'imagen_evento',
        ]
        widgets = {
            'fechaYHora': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'resultado': forms.Select(attrs={'class': 'form-select'}),
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
    
    def clean_video(self):
        """
        Si estamos editando y ya existía un archivo de vídeo,
        y el usuario no sube uno nuevo, devolvemos el previo.
        En creación, si no envía vídeo, dejamos None.
        """
        nuevo = self.cleaned_data.get('video')
        if self.instance and self.instance.pk and self.instance.video:
            if not nuevo:
                return self.instance.video
        return nuevo

    def clean_imagen_evento(self):
        """
        Igual que clean_video, pero para la imagen.
        """
        nueva = self.cleaned_data.get('imagen_evento')
        if self.instance and self.instance.pk and self.instance.imagen_evento:
            if not nueva:
                return self.instance.imagen_evento
        return nueva
        
        
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