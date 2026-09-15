from rest_framework import serializers
from users.models import Usuario
from .models import ObraSocial, Paciente


class ObraSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObraSocial
        fields = ['id', 'nombre']


class UsuarioMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'apellido', 'login', 'foto']


class PacienteSerializer(serializers.ModelSerializer):
    usuario = UsuarioMiniSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source='usuario',
        write_only=True
    )
    obra_social = ObraSocialSerializer(read_only=True)
    obra_social_id = serializers.PrimaryKeyRelatedField(
        queryset=ObraSocial.objects.all(),
        source='obra_social',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Paciente
        fields = [
            'id', 'usuario', 'usuario_id',
            'obra_social', 'obra_social_id',
            'fecha_nacimiento', 'telefono', 'correo',
            'tipo_identificacion', 'num_identificacion',
            'grupo_sanguineo',
            'contacto_emergencia_nombre', 'contacto_emergencia_numero'
        ]