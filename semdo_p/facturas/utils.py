import os
import re
from PyPDF2 import PdfReader, PdfWriter
from django.conf import settings
from .models import Persona

def dividir_pdf(archivo_pdf):
    reader = PdfReader(archivo_pdf)
    facturas = []
    
    for i in range(0, len(reader.pages), 2):
        if i + 1 >= len(reader.pages):
            break
            
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        writer.add_page(reader.pages[i + 1])
        
        output_filename = f'factura_{i//2 + 1}.pdf'
        output_path = os.path.join(settings.MEDIA_ROOT, 'facturas', output_filename)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        facturas.append({
            'path': output_path,
            'paginas': (i + 1, i + 2)
        })
    
    return facturas

def extraer_datos_factura(texto_pagina):
    datos = {
        'numero_factura': None,
        'nombre_cliente': None,
        'direccion': None,
        'periodo': None,
        'total_pagar': None
    }
    
    # Expresiones regulares para extracción de datos
    patrones = {
        'numero_factura': r'Factura Electrónica de Venta\s*([A-Z0-9]+)',
        'nombre_cliente': r'NOMBRE:\s*([^\n]+)',
        'direccion': r'DIRECCIÓN:\s*([^\n]+)',
        'periodo': r'PERIODO:\s*([^\n]+)',
        'total_pagar': r'Total a pagar\s*([$\d.,]+)'
    }
    
    for campo, patron in patrones.items():
        match = re.search(patron, texto_pagina)
        if match:
            datos[campo] = match.group(1).strip()
    
    return datos