from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from users.models import Usuario, Rol, UsuarioRol
from pacientes.models import Paciente, ObraSocial  # si ObraSocial está en otra app, cambiá el import
from profesionales.models import (
    Profesional,
    Especialidad,
    ProfesionalEspecialidad,
    Matricula,
    HorarioMedico,
)
from clinicos.models import TipoEstudio, HistoriaClinica
from turnos.models import Turno


class Command(BaseCommand):
    help = 'Carga datos de ejemplo para demo local de CliniTurnos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush-demo',
            action='store_true',
            help='No borra todo; solo evita duplicar logins de demo si ya existen',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Cargando datos de demo...')

        # ----- Roles -----
        roles = {}
        for nombre in ('ADMIN', 'MEDICO', 'PACIENTE'):
            roles[nombre], _ = Rol.objects.get_or_create(nombre=nombre)

        # ----- Obras sociales -----
        os_osde, _ = ObraSocial.objects.get_or_create(
            nombre='OSDE',
            defaults={'codigo': 'OSDE'} if self._tiene_campo(ObraSocial, 'codigo') else {},
        )
        os_swiss, _ = ObraSocial.objects.get_or_create(
            nombre='Swiss Medical',
            defaults={'codigo': 'SMG'} if self._tiene_campo(ObraSocial, 'codigo') else {},
        )
        os_pami, _ = ObraSocial.objects.get_or_create(
            nombre='PAMI',
            defaults={'codigo': 'PAMI'} if self._tiene_campo(ObraSocial, 'codigo') else {},
        )

        # ----- Especialidades -----
        esp_cardio, _ = Especialidad.objects.get_or_create(
            nombre='Cardiología',
            defaults={'descripcion': 'Enfermedades del corazón y sistema circulatorio'},
        )
        esp_clinica, _ = Especialidad.objects.get_or_create(
            nombre='Clínica Médica',
            defaults={'descripcion': 'Atención general de adultos'},
        )
        esp_lab, _ = Especialidad.objects.get_or_create(
            nombre='Laboratorio',
            defaults={'descripcion': 'Análisis clínicos y estudios de laboratorio'},
        )

        # ----- Tipos de estudio -----
        TipoEstudio.objects.get_or_create(
            nombre='Hemograma completo',
            defaults={
                'descripcion': 'Análisis de sangre básico',
                'activo': True,
                **({'duracion_min': 20} if self._tiene_campo(TipoEstudio, 'duracion_min') else {}),
            },
        )
        TipoEstudio.objects.get_or_create(
            nombre='Glucemia',
            defaults={
                'descripcion': 'Control de azúcar en sangre',
                'activo': True,
                **({'duracion_min': 15} if self._tiene_campo(TipoEstudio, 'duracion_min') else {}),
            },
        )
        TipoEstudio.objects.get_or_create(
            nombre='Orina completa',
            defaults={
                'descripcion': 'Análisis de orina',
                'activo': True,
                **({'duracion_min': 15} if self._tiene_campo(TipoEstudio, 'duracion_min') else {}),
            },
        )

        # ----- Admin -----
        admin = self._user(
            login='admin',
            password='Admin123!',
            nombre='Ana',
            apellido='Administradora',
            genero='FEMENINO',
            rol=roles['ADMIN'],
        )

                # ----- Médicos: 1 por especialidad (especialidades ya cargadas) -----
        medicos_data = [
            {
                'login': 'dra.mendez',
                'nombre': 'Laura',
                'apellido': 'Méndez',
                'genero': 'FEMENINO',
                'especialidad': 'Pediatría',
                'matricula': 'MN-20001',
                'desde': time(9, 0),
                'hasta': time(13, 0),
            },
            {
                'login': 'dr.vargas',
                'nombre': 'Diego',
                'apellido': 'Vargas',
                'genero': 'MASCULINO',
                'especialidad': 'Traumatología',
                'matricula': 'MN-20002',
                'desde': time(9, 0),
                'hasta': time(13, 0),
            },
            {
                'login': 'dra.paz',
                'nombre': 'Carolina',
                'apellido': 'Paz',
                'genero': 'FEMENINO',
                'especialidad': 'Ginecología',
                'matricula': 'MN-20003',
                'desde': time(14, 0),
                'hasta': time(18, 0),
            },
            {
                'login': 'dr.silva',
                'nombre': 'Andrés',
                'apellido': 'Silva',
                'genero': 'MASCULINO',
                'especialidad': 'Neurología',
                'matricula': 'MN-20004',
                'desde': time(9, 0),
                'hasta': time(13, 0),
            },
            {
                'login': 'dra.blanco',
                'nombre': 'Sofía',
                'apellido': 'Blanco',
                'genero': 'FEMENINO',
                'especialidad': 'Dermatología',
                'matricula': 'MN-20005',
                'desde': time(14, 0),
                'hasta': time(18, 0),
            },
            {
                'login': 'dr.garcia',
                'nombre': 'Juan',
                'apellido': 'García',
                'genero': 'MASCULINO',
                'especialidad': 'Clínica Médica',
                'matricula': 'MN-20006',
                'desde': time(9, 0),
                'hasta': time(13, 0),
            },
            {
                'login': 'dra.ortiz',
                'nombre': 'Marina',
                'apellido': 'Ortiz',
                'genero': 'FEMENINO',
                'especialidad': 'Cardiología',
                'matricula': 'MN-20007',
                'desde': time(14, 0),
                'hasta': time(18, 0),
            },
        ]

        for m in medicos_data:
            try:
                especialidad = Especialidad.objects.get(nombre=m['especialidad'])
            except Especialidad.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"No existe especialidad '{m['especialidad']}'. Saltando {m['login']}."
                    )
                )
                continue

            u = self._user(
                login=m['login'],
                password='Medico123!',
                nombre=m['nombre'],
                apellido=m['apellido'],
                genero=m['genero'],
                rol=roles['MEDICO'],
            )
            prof, _ = Profesional.objects.get_or_create(usuario=u)
            ProfesionalEspecialidad.objects.get_or_create(
                profesional=prof,
                especialidad=especialidad,
            )
            Matricula.objects.get_or_create(
                profesional=prof,
                numero_matricula=m['matricula'],
                defaults={
                    'tipo_matricula': 'NACIONAL',
                    'jurisdiccion': 'CABA',
                    'fecha_emision': date(2016, 1, 15),
                    'activa': True,
                },
            )
            self._horarios_lv(prof, m['desde'], m['hasta'], 30)
                    
        # ----- Pacientes -----
        pacientes_data = [
            {
                'login': 'paciente1',
                'password': 'Paciente123!',
                'nombre': 'Carlos',
                'apellido': 'Ruiz',
                'genero': 'MASCULINO',
                'dni': '30111222',
                'nac': date(1990, 5, 15),
                'tel': '1144556677',
                'mail': 'carlos.ruiz@mail.com',
                'os': os_osde,
            },
            {
                'login': 'paciente2',
                'password': 'Paciente123!',
                'nombre': 'María',
                'apellido': 'Fernández',
                'genero': 'FEMENINO',
                'dni': '28555666',
                'nac': date(1985, 11, 20),
                'tel': '1155667788',
                'mail': 'maria.f@mail.com',
                'os': os_swiss,
            },
            {
                'login': 'paciente3',
                'password': 'Paciente123!',
                'nombre': 'Pedro',
                'apellido': 'Sosa',
                'genero': 'MASCULINO',
                'dni': '35222333',
                'nac': date(2000, 1, 8),
                'tel': '1166778899',
                'mail': 'pedro.sosa@mail.com',
                'os': os_pami,
            },
        ]

        for p in pacientes_data:
            u = self._user(
                login=p['login'],
                password=p['password'],
                nombre=p['nombre'],
                apellido=p['apellido'],
                genero=p['genero'],
                rol=roles['PACIENTE'],
            )
            pac_defaults = {
                'tipo_identificacion': 'DNI',
                'num_identificacion': p['dni'],
                'fecha_nacimiento': p['nac'],
                'telefono': p['tel'],
                'correo': p['mail'],
            }
            if self._tiene_campo(Paciente, 'obra_social'):
                pac_defaults['obra_social'] = p['os']

            pac, created = Paciente.objects.get_or_create(
                usuario=u,
                defaults=pac_defaults,
            )
            # Historia clínica si existe el modelo y no se crea por signal
            if hasattr(pac, 'historia_clinica'):
                pass
            else:
                try:
                    HistoriaClinica.objects.get_or_create(paciente=pac)
                except Exception:
                    pass

        # ----- Slots de consulta (15 días) -----
        from django.core.management import call_command
        call_command('generar_slots_automatico', dias=15)

        self.stdout.write(self.style.SUCCESS('Demo lista.'))
        self.stdout.write('')
        self.stdout.write('Usuarios de prueba:')
        self.stdout.write('  admin / Admin123!')
        self.stdout.write('  dr.garcia / Medico123!  (cardio + clínica, 9-13)')
        self.stdout.write('  dra.lopez / Medico123!  (clínica, 14-18)')
        self.stdout.write('  paciente1 / Paciente123!  (Carlos Ruiz)')
        self.stdout.write('  paciente2 / Paciente123!  (María Fernández)')
        self.stdout.write('  paciente3 / Paciente123!  (Pedro Sosa)')

    def _tiene_campo(self, model, nombre):
        return any(f.name == nombre for f in model._meta.get_fields())

    def _user(self, login, password, nombre, apellido, genero, rol):
        u, created = Usuario.objects.get_or_create(
            login=login,
            defaults={
                'nombre': nombre,
                'apellido': apellido,
                'genero': genero,
                'estado': 'ACTIVO',
            },
        )
        if created:
            u.set_password(password)
            u.save()
        else:
            # Asegura password conocida en demo
            u.set_password(password)
            u.estado = 'ACTIVO'
            u.nombre = nombre
            u.apellido = apellido
            u.save()

        UsuarioRol.objects.get_or_create(usuario=u, rol=rol)
        return u

    def _horarios_lv(self, profesional, desde, hasta, duracion):
        for dia in ('LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES'):
            HorarioMedico.objects.get_or_create(
                profesional=profesional,
                dia_semana=dia,
                defaults={
                    'hora_desde': desde,
                    'hora_hasta': hasta,
                    'duracion_turnos_min': duracion,
                    'activo': True,
                },
            )