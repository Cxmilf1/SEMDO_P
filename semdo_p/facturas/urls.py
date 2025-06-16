from django.urls import path
from . import views

app_name = 'facturas'

urlpatterns = [
    path('lista/', views.facturas_list_view, name='lista_facturas'),
    path('eliminar/<int:factura_id>/', views.eliminar_factura, name='eliminar_factura'),
    path('enviar/', views.enviar_facturas_view, name='enviar_facturas'),
]
