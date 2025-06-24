from django.db import models
from usuarios.models import Persona, AsignacionRol, Rol
import enum  

class EstadoFacturaEnum(enum.Enum):
    pendiente = "pendiente"
    pagada = "pagada"
    vencida = "vencida"

class Factura(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
    )

    numero_factura = models.CharField(max_length=50, unique=True)
    id_emisor = models.ForeignKey(AsignacionRol, on_delete=models.CASCADE, related_name='facturas_emitidas')
    id_receptor = models.ForeignKey(AsignacionRol, on_delete=models.CASCADE, related_name='facturas_recibidas')
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    archivo_pdf = models.FileField(upload_to='facturas/')
    periodo = models.CharField(max_length=50)
    direccion = models.TextField()
    intereses_por_mora = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.numero_factura

class EnvioFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    enviado_por = models.ForeignKey(
        Persona,
        on_delete=models.SET_NULL,
        null=True,
        related_name='facturas_enviadas'
    )

    destinatario = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name='facturas_recibidas'
    )

    metodo = models.CharField(max_length=50, default='email')

class ConfiguracionCorreo(models.Model):
    mensaje_personalizado = models.TextField(
        default="""Reciba un cordial saludo de parte de SEMDO S.A. E.S.P.

Le informamos que su factura correspondiente al servicio de acueducto se encuentra disponible. A continuación, encontrará un resumen de los datos principales:

Agradecemos su confianza.

Atentamente,
SEMDO S.A. E.S.P.
Servicio de Acueducto y Alcantarillado""",
        help_text="Texto adicional del mensaje (sin incluir nombre, monto ni periodo, que se insertan automáticamente)."
    )

    def __str__(self):
        return "Configuración de correo"