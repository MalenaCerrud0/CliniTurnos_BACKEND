from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario
    Necesario porque no usamos el User estándar de Django
    """
    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError('El usuario debe tener un login')
        user = self.model(login=login, **extra_fields)
        user.set_password(password)  # Hashea la contraseña automáticamente
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('estado', 'ACTIVO')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(login, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):

    '''
    Modelo central de autenticación y datos básicos. Reemplaza al User de Django.

    - login: Es el nombre de usuario para iniciar sesión
    - estado: 'ACTIVO' o 'INACTIVO'.
        Si está inactivo, el backend le va a rechazar el login automáticamente.
    - password: Al crear o editar un usuario, mandar la clave en texto plano; el backend la encripta sola antes de guardar.
    '''

    GENERO_CHOICES = [
        ('FEMENINO', 'Femenino'),
        ('MASCULINO', 'Masculino'),
        ('NO_BINARIO', 'No binario'),
        ('PREFIERO_NO_DECIRLO', 'Prefiero no decirlo'),
    ]

    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
    ]

    # Campos según el SQL
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    foto = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES)
    login = models.CharField(max_length=50, unique=True)  # este será el "username"
    # password lo maneja AbstractBaseUser automáticamente (se guarda hasheado)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ACTIVO')
    
    # Campos para recuperación de contraseña
    codigo_recupero = models.CharField(max_length=20, null=True, blank=True)
    codigo_recupero_expira = models.DateTimeField(null=True, blank=True)

    # Campos requeridos por Django para ADMIN y permisos
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Lo sincronizamos con "estado"

    objects = UsuarioManager()

    USERNAME_FIELD = 'login'                    # Campo que se usa para login
    REQUIRED_FIELDS = ['nombre', 'apellido']    # Campos pedidos al crear superuser

    class Meta:
        db_table = 'usuarios'         # Nombre exacto de la tabla en MySQL
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.login})"

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}".strip()

    def save(self, *args, **kwargs):
        # Sincronizamos is_active con el campo estado
        self.is_active = self.estado == 'ACTIVO'
        super().save(*args, **kwargs)


class Rol(models.Model):
    """
    Roles del sistema: ADMIN, MEDICO, PACIENTE
    """
    nombre = models.CharField(
        max_length=20,
        choices=[
            ('ADMIN', 'Administrador'),
            ('MEDICO', 'Médico'),
            ('PACIENTE', 'Paciente'),
        ],
        unique=True
    )

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.nombre


class UsuarioRol(models.Model):
    '''
    TaABLA INTERMEDIA: un usuario puede tener varios roles
    OJO!! no mandar el mismo rol dos veces para el mismo usuario porque tira error (UNIQUE compuesto)
    '''
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='roles')
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='usuarios')

    class Meta:
        db_table = 'usuario_rol'
        unique_together = ('usuario', 'rol')
        verbose_name = 'Usuario-Rol'
        verbose_name_plural = 'Usuarios-Roles'

    def __str__(self):
        return f"{self.usuario} → {self.rol}"


class Permiso(models.Model):
    """
    Permisos del sistema (más granular que los roles)
    """
    descripcion = models.CharField(max_length=50)
    codigo = models.IntegerField(unique=True)

    class Meta:
        db_table = 'permisos'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class RolPermiso(models.Model):
    '''
    TABLA INTERMEDIA entre Rol y Permiso
    '''
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='permisos')
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, related_name='roles')

    class Meta:
        db_table = 'rol_permisos'
        unique_together = ('rol', 'permiso')
        verbose_name = 'Rol-Permiso'
        verbose_name_plural = 'Roles-Permisos'

    def __str__(self):
        return f"{self.rol} → {self.permiso}"


class Auditoria(models.Model):
    '''
    Registro automático (Log) de cambios importantes en el sistema
    FRONTEND: Esto es Read-Only. Solo el ADMIN consume esta data para ver la trazabilidad ("quién tocó qué")
    '''
    ACCION_CHOICES = [
        ('INSERT', 'Inserción'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='auditorias')
    tabla_afectada = models.CharField(max_length=50)
    registro_afectado_id = models.BigIntegerField()
    accion = models.CharField(max_length=10, choices=ACCION_CHOICES)
    fecha_hora = models.DateTimeField(default=timezone.now)
    valor_anterior = models.TextField(null=True, blank=True)
    valor_nuevo = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'auditorias'
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.accion} en {self.tabla_afectada} por {self.usuario}"