from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol, UsuarioRol, Permiso, RolPermiso, Auditoria


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('login', 'nombre', 'apellido', 'estado', 'is_staff')
    list_filter = ('estado', 'is_staff', 'genero')
    search_fields = ('login', 'nombre', 'apellido')
    ordering = ('login',)

    fieldsets = (
        (None, {'fields': ('login', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellido', 'foto', 'genero')}),
        ('Estado', {'fields': ('estado', 'is_active', 'is_staff', 'is_superuser')}),
        ('Recuperación', {'fields': ('codigo_recupero', 'codigo_recupero_expira')}),
        ('Fechas', {'fields': ('created_at', 'updated_at')}),
        ('Permisos', {'fields': ('groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('login', 'nombre', 'apellido', 'genero', 'password1', 'password2', 'estado'),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')


admin.site.register(Rol)
admin.site.register(UsuarioRol)
admin.site.register(Permiso)
admin.site.register(RolPermiso)
admin.site.register(Auditoria)