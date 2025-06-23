from rest_framework import serializers
from .models import Persona, Rol, AsignacionRol

class PersonaSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    creado_por_email = serializers.CharField(
        source='creado_por.email',
        read_only=True,
        allow_null=True
    )
    modificado_por_email = serializers.CharField(
        source='modificado_por.email',
        read_only=True,
        allow_null=True
    )
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Persona
        fields = [
            'id_persona',
            'nombre',
            'email',
            'direccion',
            'telefono',
            'password',
            'fecha_creacion',
            'fecha_modificacion',
            'roles',
            'creado_por_email',
            'modificado_por_email',
        ]

    def get_roles(self, obj):
        return [asignacion.id_rol.nombre for asignacion in obj.asignaciones_rol.all()]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        persona = Persona(**validated_data)
        if password:
            persona.set_password(password)
        persona.save()
        return persona

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id_rol', 'nombre', 'puede_emitir', 'puede_recibir']


class AsignacionRolSerializer(serializers.ModelSerializer):
    persona_email = serializers.CharField(
        source='id_persona.email',
        read_only=True
    )
    rol_nombre = serializers.CharField(
        source='id_rol.nombre',
        read_only=True
    )

    class Meta:
        model = AsignacionRol
        fields = [
            'id_asignacion',
            'id_persona',
            'persona_email',
            'id_rol',
            'rol_nombre'
        ]
        extra_kwargs = {
            'id_persona': {'write_only': True},
            'id_rol': {'write_only': True}
        }


class AsignacionRolCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionRol
        fields = ['id_persona', 'id_rol']
