from datetime import datetime, timedelta, time as dt_time

from django.core.management.base import BaseCommand
from django.utils import timezone

from profesionales.models import Profesional, HorarioMedico
from turnos.models import Turno


class Command(BaseCommand):
    help = (
        'Genera turnos DISPONIBLES de CONSULTA para todos los profesionales '
        'con horarios activos, en los próximos N días (default 15).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=15,
            help='Cantidad de días hacia adelante (default: 15)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué haría, sin crear turnos',
        )

    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']
        hoy = timezone.now().date()

        dias_map = {
            'LUNES': 0,
            'MARTES': 1,
            'MIERCOLES': 2,
            'JUEVES': 3,
            'VIERNES': 4,
            'SABADO': 5,
            'DOMINGO': 6,
        }

        profesionales = Profesional.objects.filter(
            usuario__estado='ACTIVO'
        ).select_related('usuario')

        total_creados = 0
        total_omitidos = 0

        for profesional in profesionales:
            horarios = HorarioMedico.objects.filter(
                profesional=profesional,
                activo=True,
            )
            if not horarios.exists():
                self.stdout.write(
                    f'  [skip] Profesional {profesional.id} sin horarios activos'
                )
                continue

            creados_prof = 0

            for i in range(dias):
                fecha = hoy + timedelta(days=i)
                dia_semana_num = fecha.weekday()  # 0=lunes ... 6=domingo

                for horario in horarios:
                    dia_horario = dias_map.get(str(horario.dia_semana).upper())
                    if dia_horario is None or dia_horario != dia_semana_num:
                        continue

                    # Duración del slot (minutos)
                    duracion = getattr(horario, 'duracion_turnos_min', None) or 30

                    hora_desde = horario.hora_desde
                    hora_hasta = horario.hora_hasta

                    # Generar slots desde hora_desde hasta hora_hasta
                    cursor = datetime.combine(fecha, hora_desde)
                    fin = datetime.combine(fecha, hora_hasta)

                    while cursor + timedelta(minutes=duracion) <= fin:
                        hora_inicio = cursor.time()
                        hora_fin = (cursor + timedelta(minutes=duracion)).time()

                        ya_existe = Turno.objects.filter(
                            profesional=profesional,
                            fecha=fecha,
                            fecha_hora_inicio=hora_inicio,
                        ).exists()

                        if ya_existe:
                            total_omitidos += 1
                        else:
                            if not dry_run:
                                Turno.objects.create(
                                    profesional=profesional,
                                    fecha=fecha,
                                    fecha_hora_inicio=hora_inicio,
                                    fecha_hora_fin=hora_fin,
                                    tipo_turno='CONSULTA',
                                    estado='DISPONIBLE',
                                    paciente=None,
                                    especialidad=None,
                                )
                            creados_prof += 1
                            total_creados += 1

                        cursor += timedelta(minutes=duracion)

            etiqueta = '[dry-run] ' if dry_run else ''
            self.stdout.write(
                f'  {etiqueta}Profesional {profesional.id} '
                f'({profesional.usuario.nombre} {profesional.usuario.apellido}): '
                f'{creados_prof} slots'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Listo. Creados: {total_creados} | Ya existían (omitidos): {total_omitidos}'
            )
        )