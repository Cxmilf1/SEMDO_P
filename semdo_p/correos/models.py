from django.db import models
from facturas.models import Factura
from datetime import datetime

class EnvioFactura(models.Model):
    ESTADO_CHOICES = [
        ('enviada', 'Enviada'),
        ('error', 'Error'),
    ]

    factura = models.OneToOneField(
        Factura,
        on_delete=models.CASCADE,
        related_name='envio_correo'  # <- esto resuelve el conflicto
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    mensaje_error = models.TextField(blank=True, null=True)
    fecha_envio = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.factura.numero_factura} - {self.estado}"
