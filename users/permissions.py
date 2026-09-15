from rest_framework.permissions import BasePermission

# OJO!! si reciben un error 403 (Forbidden) o "No tenés permiso", 
# es porque el usuario logueado está siendo bloqueado por alguna de estas clases

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(rol__nombre='ADMIN').exists()


class IsMedico(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(rol__nombre='MEDICO').exists()


class IsPaciente(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(rol__nombre='PACIENTE').exists()


class IsAdminOrMedico(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.roles.filter(rol__nombre__in=['ADMIN', 'MEDICO']).exists()