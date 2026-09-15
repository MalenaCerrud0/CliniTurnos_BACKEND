from rest_framework import serializers
from .models import Consulta, HistoriaClinica, Alergia, MedicacionHabitual

class ConsultaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()
    profesional_nombre = serializers.SerializerMethodField()
    fecha_turno = serializers.DateField(source='turno.fecha', read_only=True)
    hora_turno = serializers.TimeField(source='turno.fecha_hora_inicio', read_only=True)

    class Meta:
        model = Consulta
        fields = [
            'id',
            'turno',
            'paciente_nombre',
            'profesional_nombre',
            'fecha_turno',
            'hora_turno',
            'diagnostico',
            'plan_tratamiento',
            'indicaciones',
            'observaciones',
            'fecha_consulta',
            'estado',
        ]
        read_only_fields = ['turno', 'fecha_consulta']

    def get_paciente_nombre(self, obj):
        if obj.turno and obj.turno.paciente and obj.turno.paciente.usuario:
            return obj.turno.paciente.usuario.get_full_name()
        return None

    def get_profesional_nombre(self, obj):
        if obj.turno and obj.turno.profesional and obj.turno.profesional.usuario:
            return obj.turno.profesional.usuario.get_full_name()
        return None


class AlergiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alergia
        fields = ['id', 'historia', 'fecha_registro', 'descripcion', 'severidad']


class MedicacionHabitualSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicacionHabitual
        fields = [
            'id', 'historia', 'medicamento', 'dosis', 'frecuencia',
            'fecha_desde', 'fecha_hasta', 'motivo', 'activo',
        ]


class HistoriaClinicaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()
    informes = serializers.SerializerMethodField()
    alergias = AlergiaSerializer(many=True, read_only=True)
    medicaciones = MedicacionHabitualSerializer(many=True, read_only=True)

    class Meta:
        model = HistoriaClinica
        fields = [
            'id',
            'paciente',
            'paciente_nombre',
            'fecha_alta',
            'fecha_ult_mod',
            'alergias',
            'medicaciones',
            'informes',
        ]

    def get_paciente_nombre(self, obj):
        if obj.paciente and obj.paciente.usuario:
            return obj.paciente.usuario.get_full_name()
        return None

    def get_informes(self, obj):
        """Consultas FINALIZADAS = informes médicos de la historia."""
        consultas = Consulta.objects.filter(
            turno__paciente=obj.paciente,
            estado='FINALIZADA',
        ).select_related(
            'turno__profesional__usuario',
        ).order_by('-fecha_consulta')
        return ConsultaSerializer(consultas, many=True).data


# ----- ESTUDIOS ----- #
from .models import TipoEstudio, Estudio, EstudioDetalle


class TipoEstudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEstudio
        fields = ['id', 'nombre', 'descripcion', 'duracion_min', 'activo']


class EstudioDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstudioDetalle
        fields = ['id', 'estudio', 'descripcion', 'observaciones', 'cantidad']


class EstudioSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()
    tipo_estudio_nombre = serializers.CharField(
        source='tipo_estudio.nombre', read_only=True
    )
    detalles = EstudioDetalleSerializer(many=True, read_only=True)

    class Meta:
        model = Estudio
        fields = [
            'id',
            'tipo_estudio',
            'tipo_estudio_nombre',
            'paciente',
            'paciente_nombre',
            'turno',
            'fecha_solicitud',
            'fecha_realizacion',
            'estado',
            'observaciones',
            'detalles',
        ]
        read_only_fields = ['fecha_solicitud']

    def get_paciente_nombre(self, obj):
        if obj.paciente and obj.paciente.usuario:
            return obj.paciente.usuario.get_full_name()
        return None


# ----- DOCUMENTOS / ADJUNTOS ----- #
from .models import DocumentoClinico

class DocumentoClinicoSerializer(serializers.ModelSerializer):
    archivo_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoClinico
        fields = [
            'id',
            'historia',
            'turno',
            'consulta',
            'estudio',
            'tipo',
            'nombre',
            'archivo',
            'archivo_url',
            'fecha_carga',
            'observaciones',
        ]
        read_only_fields = ['fecha_carga']

    def get_archivo_url(self, obj):
        request = self.context.get('request')
        if obj.archivo and request:
            return request.build_absolute_uri(obj.archivo.url)
        if obj.archivo:
            return obj.archivo.url
        return None