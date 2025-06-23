from django import forms
from .models import Persona, AsignacionRol, Rol
from django.core.exceptions import ValidationError
import re

# ----------------------------
# Formulario de Login 
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
# Formulario para gestión de usuarios 
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
        if self.instance.pk:
            asignacion = self.instance.asignaciones_rol.first()
            if asignacion:
                self.fields['rol'].initial = asignacion.id_rol

    def clean_password(self):
        password = self.cleaned_data.get('password')

        if not password:
            raise ValidationError("Este campo es obligatorio.")

        # Validaciones de seguridad
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Debe contener al menos una letra mayúscula.")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Debe contener al menos una letra minúscula.")
        if not re.search(r"[0-9!@#$%^&*()_+=\[\]{};:,.<>?|`~\-]", password):
            raise ValidationError("Debe contener al menos un número o carácter especial.")
        return password

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise ValidationError("Este campo es obligatorio.")
        if any(char.isdigit() for char in nombre):
            raise ValidationError("El nombre no debe contener números.")
        return nombre.upper()

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion')
        if direccion:
            direccion = direccion.upper()
            # No prohibimos números, solo limpiamos símbolos no deseados si quieres
        return direccion


    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono and not telefono.isdigit():
            raise ValidationError("El número de teléfono debe contener solo dígitos.")
        return telefono

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
# Formulario para gestión de clientes 
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
        self.fields.pop('password', None)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Persona.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("Este correo ya está registrado.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula or not cedula.isdigit():
            raise ValidationError("La cédula debe contener solo números.")
        if Persona.objects.exclude(pk=self.instance.pk).filter(cedula=cedula).exists():
            raise ValidationError("Esta cédula ya está registrada.")
        return cedula

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise ValidationError("Este campo es obligatorio.")
        if any(char.isdigit() for char in nombre):
            raise ValidationError("El nombre no debe contener números.")
        return nombre.upper()

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion')
        if not direccion:
            raise ValidationError("La dirección es obligatoria.")
        return direccion.upper()


    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono:
            raise ValidationError("El teléfono es obligatorio.")
        if not telefono.isdigit():
            raise ValidationError("El número de teléfono debe contener solo dígitos.")
        return telefono


    def save(self, commit=True):
        persona = super().save(commit=False)
        persona.password = 'cliente_sin_acceso'

        if commit:
            persona.save()

            rol_cliente, _ = Rol.objects.get_or_create(
                nombre='Cliente',
                defaults={
                    'puede_emitir': False,
                    'puede_recibir': True
                }
            )
            AsignacionRol.objects.filter(id_persona=persona).delete()
            AsignacionRol.objects.create(id_persona=persona, id_rol=rol_cliente)

        return persona