from django.shortcuts import redirect
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', lambda request: redirect('login'), name='root_redirect'),  
  
    
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('facturas/', include('facturas.urls')),
    path('correos/', include('correos.urls')),
]
