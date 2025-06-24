from django import forms
from .models import Factura
from .models import ConfiguracionCorreo


class CargarFacturasForm(forms.Form):
    archivo_pdf = forms.FileField(
        label='Seleccionar archivo PDF',
        help_text='Archivo que contiene múltiples facturas'
    )

class SeleccionarFacturasForm(forms.Form):
    facturas = forms.ModelMultipleChoiceField(
        queryset=Factura.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

class ConfiguracionCorreoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionCorreo
        fields = ['mensaje_personalizado']
        widgets = {
            'mensaje_personalizado': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Escriba aquí el mensaje personalizado que se incluirá en el correo...'
            })
        }
        labels = {
            'mensaje_personalizado': 'Mensaje Personalizado del Correo'
        }