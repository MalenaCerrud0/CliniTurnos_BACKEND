from rest_framework import serializers
from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            'id',
            'usuario',
            'usuario_nombre',
            'turno',
            'tipo',
            'canal',
            'asunto',
            'mensaje',
            'estado',
            'fecha_programada',
            'fecha_envio',
            'intentos_reintento'
        ]
        read_only_fields = ['fecha_envio', 'intentos_reintento']

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name()
        return None