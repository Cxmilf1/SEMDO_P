from django import forms
from .models import Factura

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
