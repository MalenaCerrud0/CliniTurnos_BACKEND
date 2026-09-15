from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Notificacion
from .serializers import NotificacionSerializer


class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.select_related('usuario', 'turno').all()
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # ADMIN puede ver las notificaciones de todos
        if user.roles.filter(rol__nombre='ADMIN').exists():
            return queryset

        # PACIENTE y MÉDICO solo ven sus propias notificaciones
        return queryset.filter(usuario=user)