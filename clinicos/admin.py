from django.contrib import admin
from .models import (
    HistoriaClinica, Consulta, Alergia, MedicacionHabitual,
    TipoEstudio, Estudio, EstudioDetalle, DocumentoClinico
)

admin.site.register(HistoriaClinica)
admin.site.register(Consulta)
admin.site.register(Alergia)
admin.site.register(MedicacionHabitual)
admin.site.register(TipoEstudio)
admin.site.register(Estudio)
admin.site.register(EstudioDetalle)
admin.site.register(DocumentoClinico)