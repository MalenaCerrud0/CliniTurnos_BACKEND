from rest_framework import viewsets, generics
from rest_framework.response import Response
from .models import Usuario, Rol, UsuarioRol

from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    UsuarioSerializer, RolSerializer, UsuarioRolSerializer,
    MeSerializer, RegistroPacienteSerializer,
    CustomTokenObtainPairSerializer,
)

from rest_framework_simplejwt.views import TokenObtainPairView


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.prefetch_related('roles__rol').all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]


class UsuarioRolViewSet(viewsets.ModelViewSet):
    queryset = UsuarioRol.objects.select_related('usuario', 'rol').all()
    serializer_class = UsuarioRolSerializer
    permission_classes = [IsAuthenticated]


class MeView(generics.RetrieveUpdateAPIView):
    # Este endpoint (/me/) no recibe ningún ID en la URL
    # Sirve para:
    #   GET -> Traer los datos del usuario logueado (y su perfil de paciente asociado, si aplica)
    #   PATCH / PUT -> Actualizar nombre, apellido, foto, género y datos anidados del paciente
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegistroPacienteView(generics.CreateAPIView):
    # Endpoint que tenés que usar para la pantalla de "Crear Cuenta" o "Registro"
    # Al tener AllowAny, es el único (junto con el de login) que NO requiere mandar ningún token en los headers
    serializer_class = RegistroPacienteSerializer
    permission_classes = [AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer