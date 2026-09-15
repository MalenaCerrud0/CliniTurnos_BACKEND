from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, Rol, UsuarioRol

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre']


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, validators=[validate_password]
    )
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'login', 'nombre', 'apellido', 'genero', 'foto',
            'estado', 'password', 'roles', 'created_at',
        ]
        read_only_fields = ['created_at']

    def get_roles(self, obj):
        return list(
            obj.roles.values_list('rol__nombre', flat=True)
        )

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UsuarioRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioRol
        fields = ['id', 'usuario', 'rol']

# ----- Perfil (me) -----
class PacientePerfilSerializer(serializers.ModelSerializer):
    """Datos de paciente embebidos en /me/ (solo si el usuario es paciente)."""
    obra_social_nombre = serializers.CharField(
        source='obra_social.nombre', read_only=True, default=None
    )

    class Meta:
        from pacientes.models import Paciente
        model = Paciente
        fields = [
            'id',
            'fecha_nacimiento',
            'telefono',
            'correo',
            'tipo_identificacion',
            'num_identificacion',
            'grupo_sanguineo',
            'contacto_emergencia_nombre',
            'contacto_emergencia_numero',
            'obra_social',
            'obra_social_nombre',
        ]


class MeSerializer(serializers.ModelSerializer):
    """GET/PATCH del usuario autenticado"""
    roles = serializers.SerializerMethodField()
    paciente = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id',
            'login',
            'nombre',
            'apellido',
            'genero',
            'foto',
            'estado',
            'roles',
            'paciente',
            'created_at',
        ]
        read_only_fields = ['login', 'estado', 'created_at', 'roles']

    def get_roles(self, obj):
        return list(obj.roles.values_list('rol__nombre', flat=True))

    def get_paciente(self, obj):
        from pacientes.models import Paciente
        from pacientes.serializers import PacienteSerializer  # si ya existe uno simple

        try:
            pac = obj.paciente
        except Exception:
            return None

        # Serializer liviano inline para no depender de otro archivo
        return {
            'id': pac.id,
            'fecha_nacimiento': pac.fecha_nacimiento,
            'telefono': pac.telefono,
            'correo': pac.correo,
            'tipo_identificacion': pac.tipo_identificacion,
            'num_identificacion': pac.num_identificacion,
            'grupo_sanguineo': pac.grupo_sanguineo,
            'contacto_emergencia_nombre': pac.contacto_emergencia_nombre,
            'contacto_emergencia_numero': pac.contacto_emergencia_numero,
            'obra_social_id': pac.obra_social_id,
            'obra_social_nombre': pac.obra_social.nombre if pac.obra_social else None,
        }

    def update(self, instance, validated_data):
        # seteo de datos básicos del Usuario
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # IMPORTANTE: Para actualizar los datos del paciente desde el endpoint /me/,
        # mandar un objeto anidado en el JSON de esta forma: { "nombre": "Juan", "paciente": { "telefono": "123" } }
        request = self.context.get('request')
        if request and isinstance(request.data.get('paciente'), dict):
            from pacientes.models import Paciente
            try:
                pac = instance.paciente
            except Exception:
                pac = None
            if pac:
                pdata = request.data['paciente']
                campos = [
                    'telefono', 'correo', 'grupo_sanguineo',
                    'contacto_emergencia_nombre', 'contacto_emergencia_numero',
                    'fecha_nacimiento', 'obra_social_id',
                ]
                for c in campos:
                    if c in pdata:
                        if c == 'obra_social_id':
                            pac.obra_social_id = pdata[c]
                        else:
                            setattr(pac, c, pdata[c])
                pac.save()

        return instance

class RegistroPacienteSerializer(serializers.Serializer):

    """
    Alta pública de paciente:
    Usuario + rol PACIENTE + Paciente (+ HistoriaClinica por señal)
    """

    # IMPORTANTE JSON: Este endpoint espera que mandes todos los datos (usuario y paciente)
    # mezclados en el primer nivel del JSON. NO anidar nada.

    # Usuario
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

    # Paciente
    fecha_nacimiento = serializers.DateField()
    telefono = serializers.CharField(max_length=50, required=False, allow_blank=True)
    correo = serializers.EmailField()
    tipo_identificacion = serializers.ChoiceField(choices=[
        ('DNI', 'DNI'),
        ('PASAPORTE', 'Pasaporte'),
    ])
    num_identificacion = serializers.CharField(max_length=20)
    grupo_sanguineo = serializers.CharField(max_length=10, required=False, allow_blank=True)
    contacto_emergencia_nombre = serializers.CharField(max_length=50, required=False, allow_blank=True)
    contacto_emergencia_numero = serializers.CharField(max_length=50, required=False, allow_blank=True)
    obra_social_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_login(self, value):
        if Usuario.objects.filter(login=value).exists():
            raise serializers.ValidationError('Este login ya está en uso.')
        return value

    def validate_num_identificacion(self, value):
        from pacientes.models import Paciente
        if Paciente.objects.filter(num_identificacion=value).exists():
            raise serializers.ValidationError('Este documento ya está registrado.')
        return value

    def create(self, validated_data):
        # Backend se encarga automáticamente de separar los datos, 
        # crear el usuario, encriptar la clave, asignar el rol y crear el paciente.
        from pacientes.models import Paciente, ObraSocial
        from .models import Rol, UsuarioRol

        obra_social_id = validated_data.pop('obra_social_id', None)
        fecha_nacimiento = validated_data.pop('fecha_nacimiento')
        telefono = validated_data.pop('telefono', '')
        correo = validated_data.pop('correo')
        tipo_identificacion = validated_data.pop('tipo_identificacion')
        num_identificacion = validated_data.pop('num_identificacion')
        grupo_sanguineo = validated_data.pop('grupo_sanguineo', '')
        contacto_emergencia_nombre = validated_data.pop('contacto_emergencia_nombre', '')
        contacto_emergencia_numero = validated_data.pop('contacto_emergencia_numero', '')
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

        rol_paciente, _ = Rol.objects.get_or_create(nombre='PACIENTE')
        UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol_paciente)

        obra_social = None
        if obra_social_id:
            obra_social = ObraSocial.objects.filter(pk=obra_social_id).first()

        Paciente.objects.create(
            usuario=usuario,
            obra_social=obra_social,
            fecha_nacimiento=fecha_nacimiento,
            telefono=telefono or None,
            correo=correo,
            tipo_identificacion=tipo_identificacion,
            num_identificacion=num_identificacion,
            grupo_sanguineo=grupo_sanguineo or None,
            contacto_emergencia_nombre=contacto_emergencia_nombre or None,
            contacto_emergencia_numero=contacto_emergencia_numero or None,
        )
        # HistoriaClinica se crea por la señal post_save de Paciente

        return usuario

    def to_representation(self, instance):
        """
        instance es el Usuario creado.
        Armamos una respuesta clara sin leer campos de Paciente en el Usuario.
        """
        from pacientes.models import Paciente
        try:
            pac = instance.paciente
            paciente_data = {
                'id': pac.id,
                'fecha_nacimiento': pac.fecha_nacimiento,
                'telefono': pac.telefono,
                'correo': pac.correo,
                'tipo_identificacion': pac.tipo_identificacion,
                'num_identificacion': pac.num_identificacion,
                'obra_social_id': pac.obra_social_id,
            }
        except Exception:
            paciente_data = None

        return {
            'id': instance.id,
            'login': instance.login,
            'nombre': instance.nombre,
            'apellido': instance.apellido,
            'genero': instance.genero,
            'estado': instance.estado,
            'paciente': paciente_data,
            'mensaje': 'Paciente registrado correctamente. Ya puede iniciar sesión.',
        }

## BLOQUEO DE LOGIN SI USUARIO ESTÁ INACTIVO

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # self.user ya está autenticado por usuario/password
        user = self.user

        if getattr(user, 'estado', None) == 'INACTIVO':
            raise serializers.ValidationError(
                'Este usuario está dado de baja. Contactá al administrador.'
            )

        # Opcional: también is_active de Django
        if hasattr(user, 'is_active') and not user.is_active:
            raise serializers.ValidationError(
                'Este usuario está desactivado.'
            )

        return data