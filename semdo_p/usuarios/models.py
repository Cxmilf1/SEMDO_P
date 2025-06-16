from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission


class PersonaManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra_fields):
        if not email:
            raise ValueError('El email debe ser obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True')

        return self.create_user(email, nombre, password, **extra_fields)


class Persona(AbstractBaseUser):
    id_persona = models.BigAutoField(primary_key=True, db_column='id_persona')
    nombre = models.TextField(null=False, db_column='nombre')
    email = models.EmailField(unique=True, null=False, db_column='email')
    direccion = models.TextField(null=True, blank=True, db_column='direccion')
    telefono = models.CharField(max_length=15, null=True, blank=True, db_column='telefono')
    password = models.TextField(db_column='password')  # ya incluido por AbstractBaseUser, pero aquí se respeta columna
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='fecha_creacion')
    fecha_modificacion = models.DateTimeField(auto_now=True, db_column='fecha_modificacion')
    creado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='creado_por',
        related_name='personas_creadas'
    )
    modificado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='modificado_por',
        related_name='personas_modificadas'
    )
    cedula = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Nuevo campo

    def __str__(self):
        return self.nombre
        
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    objects = PersonaManager()

    class Meta:
        db_table = 'persona'

    def __str__(self):
        return f"{self.nombre} ({self.email})"




class Rol(models.Model):
    id_rol = models.BigAutoField(primary_key=True, db_column='id_rol')
    nombre = models.TextField(unique=True, db_column='nombre')
    puede_emitir = models.BooleanField(default=False, db_column='puede_emitir')
    puede_recibir = models.BooleanField(default=False, db_column='puede_recibir')

    class Meta:
        db_table = 'rol'

    def __str__(self):
        return self.nombre


class AsignacionRol(models.Model):
    id_asignacion = models.BigAutoField(primary_key=True, db_column='id_asignacion')
    id_persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        db_column='id_persona',
        related_name='asignaciones_rol'
    )
    id_rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        db_column='id_rol'
    )

    class Meta:
        db_table = 'asignacionrol'
        unique_together = ('id_persona', 'id_rol')

    def __str__(self):
        return f"{self.id_persona.nombre} - {self.id_rol.nombre}"