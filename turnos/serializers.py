from rest_framework import serializers
from .models import Turno, FechaBloqueada
from pacientes.models import Paciente
from profesionales.models import Profesional, Especialidad


class TurnoSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()
    profesional_nombre = serializers.SerializerMethodField()
    especialidad_nombre = serializers.CharField(
        source='especialidad.nombre', read_only=True, default=None
    )
    obra_social_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Turno
        fields = [
            'id',
            'paciente', 'paciente_nombre',
            'profesional', 'profesional_nombre',
            'especialidad', 'especialidad_nombre',
            'obra_social_nombre',
            'tipo_turno',
            'fecha',
            'estado',
            'fecha_hora_inicio',
            'fecha_hora_fin',
            'comentario',
        ]
        read_only_fields = ['estado']

    def get_paciente_nombre(self, obj):
        if obj.paciente and obj.paciente.usuario:
            return obj.paciente.usuario.get_full_name()
        return None

    def get_profesional_nombre(self, obj):
        if obj.profesional and obj.profesional.usuario:
            return obj.profesional.usuario.get_full_name()
        return None

    def get_obra_social_nombre(self, obj):
        if obj.paciente and obj.paciente.obra_social:
            return obj.paciente.obra_social.nombre
        return None


class FechaBloqueadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FechaBloqueada
        fields = ['id', 'profesional', 'fecha_desde', 'fecha_hasta', 'motivo']