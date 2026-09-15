from rest_framework import serializers
from users.models import Usuario, Rol, UsuarioRol
from .models import (
    Especialidad, Profesional, ProfesionalEspecialidad,
    Matricula, HorarioMedico
)

from django.contrib.auth.password_validation import validate_password


class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ['id', 'nombre', 'descripcion']


class UsuarioMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'apellido', 'login', 'foto']


class MatriculaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matricula
        fields = [
            'id', 'profesional', 'numero_matricula', 'tipo_matricula',
            'jurisdiccion', 'fecha_emision', 'fecha_vencimiento', 'activa'
        ]


class HorarioMedicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioMedico
        fields = [
            'id', 'profesional', 'dia_semana', 'hora_desde', 'hora_hasta',
            'duracion_turnos_min', 'activo'
        ]


class ProfesionalEspecialidadSerializer(serializers.ModelSerializer):
    especialidad = EspecialidadSerializer(read_only=True)
    especialidad_id = serializers.PrimaryKeyRelatedField(
        queryset=Especialidad.objects.all(),
        source='especialidad',
        write_only=True
    )
    profesional_id = serializers.PrimaryKeyRelatedField(
        queryset=Profesional.objects.all(),
        source='profesional',
        write_only=True
    )

    class Meta:
        model = ProfesionalEspecialidad
        fields = ['id', 'profesional_id', 'especialidad', 'especialidad_id']


class ProfesionalSerializer(serializers.ModelSerializer):
    usuario = UsuarioMiniSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source='usuario',
        write_only=True
    )
    especialidades = ProfesionalEspecialidadSerializer(
        many=True, 
        read_only=True
    )
    matriculas = MatriculaSerializer(many=True, read_only=True)
    horarios = HorarioMedicoSerializer(many=True, read_only=True)

    class Meta:
        model = Profesional
        fields = [
            'id', 'usuario', 'usuario_id',
            'especialidades', 'matriculas', 'horarios'
        ]


class AltaProfesionalSerializer(serializers.Serializer):
    # USUARIO
    login = serializers.CharField(max_length=50)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    nombre = serializers.CharField(max_length=50)
    apellido = serializers.CharField(max_length=50)
    genero = serializers.ChoiceField(choices=[
        ('FEMENINO', 'Femenino'),
        ('MASCULINO', 'Masculino'),
        ('NO_BINARIO', 'No binario'),
        ('PREFIERO_NO_DECIRLO', 'Prefiero no decirlo'),
    ])

    # ESPECIALIDADES (ids)
    especialidad_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )

    # MATRÍCULA (opcional)
    numero_matricula = serializers.CharField(required=False, allow_blank=True)
    tipo_matricula = serializers.ChoiceField(
        choices=[('NACIONAL', 'Nacional'), ('PROVINCIAL', 'Provincial')],
        required=False,
    )
    jurisdiccion = serializers.CharField(required=False, allow_blank=True)
    fecha_emision = serializers.DateField(required=False, allow_null=True)
    fecha_vencimiento = serializers.DateField(required=False, allow_null=True)

    def validate_login(self, value):
        if Usuario.objects.filter(login=value).exists():
            raise serializers.ValidationError('Este login ya está en uso.')
        return value

    def validate_numero_matricula(self, value):
        if value and Matricula.objects.filter(numero_matricula=value).exists():
            raise serializers.ValidationError('Ese número de matrícula ya existe.')
        return value

    def create(self, validated_data):
        especialidad_ids = validated_data.pop('especialidad_ids', [])
        numero_matricula = validated_data.pop('numero_matricula', '') or ''
        tipo_matricula = validated_data.pop('tipo_matricula', None)
        jurisdiccion = validated_data.pop('jurisdiccion', '') or None
        fecha_emision = validated_data.pop('fecha_emision', None)
        fecha_vencimiento = validated_data.pop('fecha_vencimiento', None)
        password = validated_data.pop('password')

        usuario = Usuario(
            login=validated_data['login'],
            nombre=validated_data['nombre'],
            apellido=validated_data['apellido'],
            genero=validated_data['genero'],
            estado='ACTIVO',
        )
        usuario.set_password(password)
        usuario.save()

        rol_medico, _ = Rol.objects.get_or_create(nombre='MEDICO')
        UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol_medico)

        profesional = Profesional.objects.create(usuario=usuario)

        for esp_id in especialidad_ids:
            ProfesionalEspecialidad.objects.get_or_create(
                profesional=profesional,
                especialidad_id=esp_id,
            )

        if numero_matricula:
            if not tipo_matricula:
                raise serializers.ValidationError(
                    {'tipo_matricula': 'Obligatorio si enviás numero_matricula.'}
                )
            Matricula.objects.create(
                profesional=profesional,
                numero_matricula=numero_matricula,
                tipo_matricula=tipo_matricula,
                jurisdiccion=jurisdiccion,
                fecha_emision=fecha_emision,
                fecha_vencimiento=fecha_vencimiento,
                activa=True,
            )

        return profesional

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'usuario_id': instance.usuario_id,
            'login': instance.usuario.login,
            'nombre': instance.usuario.nombre,
            'apellido': instance.usuario.apellido,
            'estado_usuario': instance.usuario.estado,
            'mensaje': 'Profesional dado de alta correctamente',
        }

class BajaProfesionalSerializer(serializers.Serializer):
    """Solo confirma la acción; el id va en la URL."""
    pass