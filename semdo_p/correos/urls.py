from django.urls import path
from . import views

app_name = 'correos'

urlpatterns = [
    path('historial/', views.historial_envios_view, name='historial_envios'),
]
