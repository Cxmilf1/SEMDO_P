from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout  
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from .models import Persona, Rol, AsignacionRol
from .serializers import (
    PersonaSerializer,
    AsignacionRolSerializer,
    AsignacionRolCreateSerializer
)
from .forms import LoginForm, UsuarioForm, ClienteForm


# Vistas Web (HTML)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = None
            try:
                persona = Persona.objects.get(email=email)
                if persona.check_password(password):
                    user = persona
            except Persona.DoesNotExist:
                user = None

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, "Credenciales inválidas. Intente nuevamente.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def home_view(request):
    return render(request, 'home.html')



@login_required
def home_view(request):
    return render(request, 'home.html')


@login_required
def listar_personas(request):
    search = request.GET.get('search', '')

    personas = Persona.objects.filter(
        Q(nombre__icontains=search) | Q(email__icontains=search)
    ).exclude(
        asignaciones_rol__id_rol__nombre__iexact='cliente'  
    ).prefetch_related('asignaciones_rol__id_rol').distinct()

    return render(request, 'usuarios.html', {
        'usuarios': personas,
        'search': search
    })



@login_required
def crear_persona(request):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('listar_usuarios')

    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            persona = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                persona.set_password(password)
            persona.save()

            rol_seleccionado = form.cleaned_data.get('rol')
            if rol_seleccionado:
                AsignacionRol.objects.create(id_persona=persona, id_rol=rol_seleccionado)

            messages.success(request, 'Persona creada exitosamente')
            return redirect('listar_usuarios')
    else:
        form = UsuarioForm()

    return render(request, 'crear_editar_usuario.html', {
        'form': form,
        'titulo': 'Crear Persona'
    })


@login_required
def editar_persona(request, id):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('listar_usuarios')

    persona = get_object_or_404(Persona, id_persona=id)

    # ✅ OBTENER EL ROL ACTUAL DE LA PERSONA
    rol_actual = persona.asignaciones_rol.first().id_rol if persona.asignaciones_rol.exists() else None

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=persona)
        if form.is_valid():
            persona = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                persona.set_password(password)
            persona.save()
            rol_nuevo = form.cleaned_data.get('rol')
            AsignacionRol.objects.update_or_create(
                id_persona=persona,
                defaults={'id_rol': rol_nuevo}
            )

            messages.success(request, 'Persona actualizada exitosamente')
            return redirect('listar_usuarios')
    else:
        form = UsuarioForm(instance=persona, initial={'rol': rol_actual})

    return render(request, 'crear_editar_usuario.html', {
        'form': form,
        'titulo': 'Editar Persona',
        'usuario': persona
    })


@login_required
def eliminar_persona(request, id):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('listar_usuarios')

    persona = get_object_or_404(Persona, id_persona=id)

    if request.method == 'POST':
        try:
            # Eliminar asignaciones de roles primero
            AsignacionRol.objects.filter(id_persona=persona).delete()
            
            # Eliminar la persona
            persona.delete()
            
            messages.success(request, f'Usuario {persona.nombre} eliminado exitosamente')
            return redirect('listar_usuarios')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar usuario: {str(e)}')
            return redirect('listar_usuarios')

    return render(request, 'eliminar_usuario.html', {'usuario': persona})

@login_required
def listar_clientes(request):
    search = request.GET.get('search', '')
    
    rol_cliente = Rol.objects.filter(nombre='Cliente').first()
    
    # Obtener clientes (aunque no exista rol)
    clientes = Persona.objects.filter(
        asignaciones_rol__id_rol=rol_cliente
    ) if rol_cliente else Persona.objects.none()
    
    # Aplicar búsqueda
    if search:
        clientes = clientes.filter(
            Q(nombre__icontains=search) | 
            Q(email__icontains=search) |
            Q(cedula__icontains=search)  
        )
    
    return render(request, 'clientes.html', {  
        'clientes': clientes,
        'search': search
    })


@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            # Guardar cliente con rol automático
            cliente = form.save(commit=False)
            
            # Crear rol de cliente si no existe
            rol_cliente, created = Rol.objects.get_or_create(
                nombre='Cliente',
                defaults={'puede_emitir': False, 'puede_recibir': True}
            )
            
            # Guardar cliente
            cliente.save()
            
            # Asignar rol automáticamente
            AsignacionRol.objects.create(id_persona=cliente, id_rol=rol_cliente)
            
            messages.success(request, 'Cliente creado exitosamente')
            return redirect('listar_clientes')
    else:
        form = ClienteForm()

    return render(request, 'crear_editar_cliente.html', {
        'form': form,
        'titulo': '➕ Crear Nuevo Cliente'
    })

@login_required
def editar_cliente(request, id):
    cliente = get_object_or_404(Persona, id_persona=id)

    # Verificar si el cliente tiene rol de cliente
    asignacion_cliente = cliente.asignaciones_rol.filter(id_rol__nombre='Cliente').first()
    if not asignacion_cliente:
        messages.warning(request, 'Esta persona no es un cliente registrado')
        return redirect('listar_clientes')

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente_actualizado = form.save(commit=False)
            cliente_actualizado.save()

            # Asegurarse de que conserve la asignación al rol Cliente
            rol_cliente = Rol.objects.get(nombre='Cliente')
            AsignacionRol.objects.update_or_create(
                id_persona=cliente_actualizado,
                id_rol=rol_cliente,
                defaults={}
            )

            messages.success(request, 'Cliente actualizado exitosamente')
            return redirect('listar_clientes')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'crear_editar_cliente.html', {
        'form': form,
        'titulo': '✏️ Editar Cliente'
    })


@login_required
def eliminar_cliente(request, id):
    cliente = get_object_or_404(Persona, id_persona=id)
    
    # Verificar si el cliente tiene rol de cliente
    if not cliente.asignaciones_rol.filter(id_rol__nombre='Cliente').exists():
        messages.warning(request, 'Esta persona no es un cliente registrado')
        return redirect('listar_clientes')

    if request.method == 'POST':
        # Eliminar asignaciones de rol primero
        cliente.asignaciones_rol.filter(id_rol__nombre='Cliente').delete()
        
        # Eliminar cliente
        cliente.delete()
        
        messages.success(request, 'Cliente eliminado exitosamente')
        return redirect('listar_clientes')

    return render(request, 'cliente_confirmar_eliminar.html', {
        'cliente': cliente
    })

@login_required
def eliminar_clientes_seleccionados(request):
    if request.method == 'POST':
        ids = request.POST.getlist('clientes_seleccionados')
        clientes_eliminados = 0

        for id_str in ids:
            try:
                cliente = Persona.objects.get(id_persona=id_str)
                if cliente.asignaciones_rol.filter(id_rol__nombre='Cliente').exists():
                    cliente.asignaciones_rol.filter(id_rol__nombre='Cliente').delete()
                    cliente.delete()
                    clientes_eliminados += 1
            except Persona.DoesNotExist:
                continue

        messages.success(request, f'{clientes_eliminados} cliente(s) eliminados exitosamente.')
        return redirect('listar_clientes')

    messages.error(request, 'Método no permitido.')
    return redirect('listar_clientes')

# Vistas API (REST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def registrar_persona(request):
    serializer = PersonaSerializer(data=request.data)
    if serializer.is_valid():
        persona = serializer.save()
        refresh = RefreshToken.for_user(persona)
        return Response({
            'user': PersonaSerializer(persona).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_personas_api(request):
    personas = Persona.objects.all()
    serializer = PersonaSerializer(personas, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_persona_api(request, id):
    persona = get_object_or_404(Persona, id_persona=id)
    serializer = PersonaSerializer(persona)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def actualizar_persona_api(request, id):
    persona = get_object_or_404(Persona, id_persona=id)
    serializer = PersonaSerializer(persona, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def eliminar_persona_api(request, id):
    persona = get_object_or_404(Persona, id_persona=id)
    persona.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
