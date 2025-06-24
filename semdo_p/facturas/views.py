import os
import re
import jwt
from django.db.models import Exists, OuterRef
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from facturas.models import Factura, EnvioFactura
from usuarios.models import AsignacionRol, Rol, Persona
from PyPDF2 import PdfReader, PdfWriter
from .forms import CargarFacturasForm
from django.http import JsonResponse
from django.core.mail import send_mail, EmailMessage
from correos.models import EnvioFactura

# -------------------------------
# Utilidades para dividir y extraer datos del PDF
# -------------------------------

def dividir_pdf(ruta_pdf):
    reader = PdfReader(ruta_pdf)
    total_paginas = len(reader.pages)
    facturas = []

    for i in range(0, total_paginas, 2):
        if i + 1 < total_paginas:
            texto_pagina1 = reader.pages[i].extract_text()
            datos = extraer_datos_factura(texto_pagina1)
            nombre_archivo = f"factura_{datos.get('numero_factura', i//2 + 1)}.pdf"
            ruta_destino = os.path.join(settings.MEDIA_ROOT, 'facturas', nombre_archivo)
            os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)

            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            writer.add_page(reader.pages[i + 1])
            with open(ruta_destino, 'wb') as f:
                writer.write(f)

            facturas.append({
                'ruta': ruta_destino,
                'nombre': nombre_archivo,
                'paginas': (i + 1, i + 2),
                'datos': datos
            })
    return facturas

def extraer_datos_factura(texto):
    datos = {
        'numero_factura': None,
        'nombre_cliente': None,
        'direccion': None,
        'periodo': None,
        'total_pagar': None,
        'fecha_emision': None,
        'fecha_vencimiento': None
    }

    patrones = {
        'numero_factura': r'Factura Electrónica de Venta\s+([A-Z0-9-]+)',
        'nombre_cliente': r'Número de identificación en la empresa\s*([A-ZÑÁÉÍÓÚ ]{5,})',
        'direccion': r'DIRECCIÓN:\s*([^\n]+)',
        'periodo': r'PERIODO:\s*([^\n]+)',
        'total_pagar': r'(?:TOTAL A PAGAR|Total a pagar)[\s\S]*?\$([\d.,]+)(?=\s*[\n\r<])',
        'fecha_emision': r'FECHA EMISIÓN:\s*([^\n]+)',
        'fecha_vencimiento': r'FECHA LÍMITE DE PAGO\s*([^\n]+)'
    }

    for campo, patron in patrones.items():
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            valor = match.group(1).strip()
            if campo == 'total_pagar':
                valor = float(valor.replace('$', '').replace(',', '').replace('.', '', valor.count('.') - 1))
            elif campo in ['fecha_emision', 'fecha_vencimiento']:
                valor = parsear_fecha(valor)
            datos[campo] = valor

    return datos

def parsear_fecha(fecha_str):
    meses = {
        'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
        'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
    }

    try:
        for mes_nombre, mes_num in meses.items():
            if mes_nombre in fecha_str:
                partes = fecha_str.replace(mes_nombre, '').strip().split('-')
                dia = int(partes[0].strip())
                anio = int(f"20{partes[1].strip()}")
                return datetime(anio, mes_num, dia).date()

        if len(fecha_str.split('-')) == 3:
            dia, mes, anio = fecha_str.split('-')
            return datetime(2000 + int(anio), int(mes), int(dia)).date()
    except (ValueError, IndexError):
        pass

    return datetime.now().date()

# -------------------------------
# Vista Web: listar y cargar facturas desde HTML
# -------------------------------

def facturas_list_view(request):
    form = CargarFacturasForm()
    
    if request.method == 'POST':
        form = CargarFacturasForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_pdf']
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_facturas'))
            nombre_archivo = fs.save(archivo.name, archivo)
            ruta_pdf = fs.path(nombre_archivo)

            try:
                facturas_divididas = dividir_pdf(ruta_pdf)
            except Exception as e:
                fs.delete(nombre_archivo)
                messages.error(request, f'Error al procesar PDF: {e}')
                return redirect('facturas:lista_facturas')

            fs.delete(nombre_archivo)
            rol_emisor = Rol.objects.filter(puede_emitir=True).first()
            rol_receptor = Rol.objects.filter(puede_recibir=True).first()
            emisor = Persona.objects.filter(is_staff=True).first()
            asignacion_emisor, _ = AsignacionRol.objects.get_or_create(id_persona=emisor, id_rol=rol_emisor)

            facturas_creadas = []
            facturas_duplicadas = []
            facturas_erroneas = []
            
            for f in facturas_divididas:
                datos = f.get('datos', {})
                nombre_cliente = datos.get('nombre_cliente')
                
                if not nombre_cliente:
                    continue

                numero_factura = datos.get('numero_factura')
                if not numero_factura or Factura.objects.filter(numero_factura=numero_factura).exists():
                    if numero_factura:
                        facturas_duplicadas.append(numero_factura)
                    else:
                        facturas_erroneas.append(f"Páginas {f['paginas']}")
                    continue

                cliente, creado = Persona.objects.get_or_create(
                    nombre=nombre_cliente,
                    defaults={
                        'direccion': datos.get('direccion', ''),
                        'email': f"{nombre_cliente.replace(' ', '.').lower()}@ejemplo.com",
                        'password': 'cliente_sin_acceso',
                        'is_staff': False  
                        'is_superuser': False  
                    }
                )

                if creado:
                    AsignacionRol.objects.filter(id_persona=cliente).delete()  # 🔥 Eliminamos roles previos

                rol_cliente, _ = Rol.objects.get_or_create(nombre='Cliente', defaults={
                    'puede_emitir': False,
                    'puede_recibir': True
                })

                asignacion_receptor, _ = AsignacionRol.objects.get_or_create(id_persona=cliente, id_rol=rol_cliente)
                ruta_relativa = os.path.relpath(f['ruta'], settings.MEDIA_ROOT)

                try:
                    factura = Factura.objects.create(
                        numero_factura=numero_factura,
                        id_emisor=asignacion_emisor,
                        id_receptor=asignacion_receptor,
                        fecha_emision=datos.get('fecha_emision', datetime.now().date()),
                        fecha_vencimiento=datos.get('fecha_vencimiento', datetime.now().date() + timedelta(days=30)),
                        monto=datos.get('total_pagar', 0.0),
                        estado='pendiente',
                        archivo_pdf=ruta_relativa,
                        periodo=datos.get('periodo', datetime.now().strftime('%Y-%m')),
                        direccion=datos.get('direccion', '')
                    )
                    facturas_creadas.append(factura)
                except Exception as e:
                    facturas_erroneas.append(f"{numero_factura} - {str(e)}")

            mensaje = ""
            if facturas_creadas:
                mensaje += f"✅ {len(facturas_creadas)} factura(s) procesada(s) correctamente. "
            if facturas_duplicadas:
                mensaje += f"❌ Facturas duplicadas: {', '.join(facturas_duplicadas)}. "
            if facturas_erroneas:
                mensaje += f"⚠️ Errores: {', '.join(facturas_erroneas)}"

            messages.info(request, mensaje.strip())
            return redirect('facturas:lista_facturas')

    envios = EnvioFactura.objects.filter(factura=OuterRef('pk'))
    facturas = Factura.objects.annotate(ya_enviada=Exists(envios)).filter(ya_enviada=False).order_by('-fecha_creacion')

    return render(request, 'listado_facturas.html', {
        'facturas': facturas,
        'form': form
    })

# -------------------------------
# Vista Web: eliminar factura
# -------------------------------

def eliminar_factura(request, factura_id):
    try:
        factura = Factura.objects.get(pk=factura_id)
        factura.delete()
        return JsonResponse({'success': True, 'message': 'Factura eliminada correctamente.'})
    except Factura.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'La factura no existe.'})

# -------------------------------
# Vista Web: enviar correo
# -------------------------------

@csrf_exempt
def enviar_facturas_view(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        enviadas = 0

        config = ConfiguracionCorreo.objects.first()
        mensaje_personalizado = config.mensaje_personalizado if config else ""

        for factura_id in ids:
            factura = Factura.objects.filter(id=factura_id).first()
            if factura and factura.id_receptor.id_persona.email:
                cliente = factura.id_receptor.id_persona
                nombre_cliente = cliente.nombre
                total_pagar = factura.monto
                periodo = factura.periodo

                cuerpo = f"""
Estimado/a {nombre_cliente}:

{mensaje_personalizado}

Nombre del cliente: {nombre_cliente}
Valor a pagar: ${total_pagar:,.2f}
Rango de pago oportuno: {periodo}
                """

                email = EmailMessage(
                    subject=f"Factura de Acueducto y Alcantarillado {factura.numero_factura}",
                    body=cuerpo,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[cliente.email]
                )

                ruta_absoluta = os.path.join(settings.MEDIA_ROOT, factura.archivo_pdf.name)
                email.attach_file(ruta_absoluta)
                email.send(fail_silently=False)

                factura.estado = 'enviada'
                factura.save()

                EnvioFactura.objects.create(
                    factura=factura,
                    destinatario=cliente,
                    fecha_envio=timezone.now()
                )

                enviadas += 1

        return JsonResponse({'mensaje': f'✅ {enviadas} factura(s) enviada(s) correctamente.'})
