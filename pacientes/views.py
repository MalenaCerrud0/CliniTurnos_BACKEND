from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import ObraSocial, Paciente
from .serializers import ObraSocialSerializer, PacienteSerializer


class ObraSocialViewSet(viewsets.ModelViewSet):
    queryset = ObraSocial.objects.all().order_by('nombre')
    serializer_class = ObraSocialSerializer
    permission_classes = [IsAuthenticated]


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.select_related('usuario', 'obra_social').all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]