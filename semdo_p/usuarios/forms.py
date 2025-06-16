from django import forms
from .models import Persona, AsignacionRol, Rol

# ----------------------------
# Formulario de Login (ya existente en el proyecto)
# ----------------------------
class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Correo Electrónico',
            'class': 'form-input',
            'required': True,
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Contraseña',
            'class': 'form-input',
            'required': True,
        })
    )


# ----------------------------
# Formulario para gestión de usuarios (nuevo)
# ----------------------------
class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        required=False,
        help_text="Dejar vacío para no cambiar la contraseña."
    )
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        label='Rol',
        required=True,
        empty_label="seleccione un rol"
    )

    class Meta:
        model = Persona
        fields = ['nombre', 'email', 'telefono', 'direccion', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar campo rol con la asignación actual, si existe
        if self.instance.pk:
            asignacion = self.instance.asignaciones_rol.first()
            if asignacion:
                self.fields['rol'].initial = asignacion.id_rol
    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Para usuarios nuevos, la contraseña es obligatoria
        if not self.instance.pk and not password:
            raise forms.ValidationError("La contraseña es obligatoria para nuevos usuarios.")
        return password

    def save(self, commit=True):
        persona = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            persona.set_password(password)
        if commit:
            persona.save()
            rol = self.cleaned_data['rol']
            AsignacionRol.objects.update_or_create(
                id_persona=persona,
                defaults={'id_rol': rol}
            )
        return persona


# ----------------------------
# Formulario para gestión de clientes (nuevo)
# ----------------------------
class ClienteForm(forms.ModelForm):
    cedula = forms.CharField(
        label='Cédula/RUC',
        max_length=20,
        required=True,
        help_text='Ingrese la cédula o RUC del cliente'
    )

    class Meta:
        model = Persona
        fields = ['nombre', 'email', 'telefono', 'direccion', 'cedula']
        labels = {
            'cedula': 'Cédula/RUC',
            'nombre': 'Nombre Completo',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección'
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Eliminar validación de contraseña para clientes
        self.fields.pop('password', None)
        
    def save(self, commit=True):
        # Guardar persona sin contraseña
        persona = super().save(commit=False)
        persona.password = 'cliente_sin_acceso'  # Valor dummy no utilizable
        
        if commit:
            persona.save()
            
            # Asignar rol de cliente automáticamente
            rol_cliente, created = Rol.objects.get_or_create(
                nombre='Cliente',
                defaults={
                    'puede_emitir': False,
                    'puede_recibir': True
                }
            )
            AsignacionRol.objects.get_or_create(
                id_persona=persona,
                id_rol=rol_cliente
            )
            
        return persona