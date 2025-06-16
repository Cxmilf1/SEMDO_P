from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # --------------------------------------------------
    # Vistas Web (HTML)
    # --------------------------------------------------

    # Autenticación
    path('login/', views.login_view, name='login'),              
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),                  

    # Gestión de usuarios (vistas web)
    path('panel/usuarios/', views.listar_personas, name='listar_usuarios'),
    path('panel/usuarios/crear/', views.crear_persona, name='crear_usuario'),
    path('panel/usuarios/editar/<int:id>/', views.editar_persona, name='editar_usuario'),
    path('panel/usuarios/eliminar/<int:id>/', views.eliminar_persona, name='eliminar_usuario'),

    # Gestión de clientes (vistas web)
    path('panel/clientes/', views.listar_clientes, name='listar_clientes'),
    path('panel/clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('panel/clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('panel/clientes/eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),

    # --------------------------------------------------
    # Vistas API (REST)
    # --------------------------------------------------

    # JWT Refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Gestión de usuarios API
    path('api/registrar/', views.registrar_persona, name='registrar_persona'),
    path('api/usuarios/', views.lista_personas_api, name='listar_personas_api'),
    path('api/usuarios/<int:id>/', views.detalle_persona_api, name='detalle_persona_api'),
    path('api/usuarios/actualizar/<int:id>/', views.actualizar_persona_api, name='actualizar_persona_api'),
    path('api/usuarios/eliminar/<int:id>/', views.eliminar_persona_api, name='eliminar_persona_api'),
]
