from django.shortcuts import render
from facturas.models import EnvioFactura

def historial_envios_view(request):
    envios = EnvioFactura.objects.select_related('factura', 'factura__id_receptor__id_persona')\
                                  .order_by('-fecha_envio')
    return render(request, 'historial_envios.html', {'envios': envios})




