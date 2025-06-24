from django.shortcuts import render, redirect
from facturas.models import EnvioFactura
from django.db.models import Q

def historial_envios_view(request):
    query = request.GET.get('q', '')
    
    envios = EnvioFactura.objects.select_related(
        'factura',
        'factura__id_receptor',
        'factura__id_receptor__id_persona'
    ).order_by('-fecha_envio')

    if query:
        envios = envios.filter(
            Q(factura__numero_factura__icontains=query) |
            Q(factura__id_receptor__id_persona__nombre__icontains=query)
        )

    if request.method == 'POST':
        seleccionados = request.POST.getlist('seleccionados')
        EnvioFactura.objects.filter(id__in=seleccionados).delete()
        return redirect('correos:historial_envios')  
        
    return render(request, 'historial_envios.html', {
        'envios': envios,
        'query': query
    })
