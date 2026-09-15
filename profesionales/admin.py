from django.contrib import admin
from .models import (
    Especialidad, Profesional, ProfesionalEspecialidad,
    ProfesionalPaciente, Matricula, HorarioMedico
)

admin.site.register(Especialidad)
admin.site.register(Profesional)
admin.site.register(ProfesionalEspecialidad)
admin.site.register(ProfesionalPaciente)
admin.site.register(Matricula)
admin.site.register(HorarioMedico)