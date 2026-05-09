from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone



# --- GESTOR DE USUARIOS ---
class UsuarioManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('El campo username es obligatorio')

        tipo_usuario_obj = extra_fields.pop('tipo_usuario', None)
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)

        if tipo_usuario_obj:
            user.tipo_usuario = tipo_usuario_obj

        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuario debe tener is_superuser=True.')

        return self.create_user(username, password, **extra_fields)

# --- MODELOS AUXILIARES ---

class TipoUsuario(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

# IMPORTANTE: Movemos Asignatura ANTES de Usuario para poder relacionarla
class Asignatura(models.Model):
    nombre = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nombre # Quitamos el f-string para que sea más limpio en el admin

# --- MODELO PRINCIPAL DE USUARIO ---
class Usuario(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)    
    celular = models.CharField(max_length=14, blank=True)
    
    tipo_usuario = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE, null=True, blank=True)
    
    # NUEVO CAMPO: Relación Muchos a Muchos con Asignaturas
    # blank=True permite que estudiantes o admins no tengan asignaturas obligatorias
    asignaturas = models.ManyToManyField(Asignatura, blank=True, related_name='docentes')

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nombre', 'apellido']

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.username})"




class Disponibilidad(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    docente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='horarios_disponibles')
    fecha = models.DateField(default=timezone.now)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    

# 2. Disponibilidad Múltiple (Regla de repetición semanal) - ¡NUEVO, AÑADIR ESTO!
class DisponibilidadMultiple(models.Model):
    fecha_inicio = models.DateField(help_text="Fecha de inicio de la repetición semanal")
    fecha_fin = models.DateField(help_text="Fecha de término de la repetición semanal")
    # Usaremos IntegerField para el día de la semana (1=Lunes, 7=Domingo)
    dia_semana = models.IntegerField(help_text="1=Lunes, 2=Martes, ..., 7=Domingo")
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    docente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='disponibilidades_multiples')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Regla Semanal {self.docente} - Día {self.dia_semana} ({self.hora_inicio}-{self.hora_fin})"
    

# --- MODELOS DE CLASES Y PAGOS (Se mantienen igual) ---
class ClasesAgendadas(models.Model):
    fecha = models.DateTimeField()
    costo = models.IntegerField()
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='clases_estudiante')
    docente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='clases_docente')
    estado = models.CharField(max_length=20, default='AGEN')
    timestamp = models.DateTimeField(auto_now_add=True)

    # Campos de borrado lógico (Añadidos en turnos anteriores)
    oculto_para_estudiante = models.BooleanField(default=False)
    oculto_para_docente = models.BooleanField(default=False)

    # Enlace ForeignKey (Añadido en turnos anteriores para optimización)
    horario = models.ForeignKey(Disponibilidad, on_delete=models.SET_NULL, null=True, blank=True, related_name='clase_registrada')
    datos_pizarra = models.TextField(null=True, blank=True)
    historial_chat = models.TextField(default="[]") # Guardaremos una lista de objetos JSON

    def __str__(self):
        return f"Clase {self.asignatura} - {self.fecha}"
    


class ComprobantePago(models.Model):
    class EstadoPago(models.TextChoices):
        PENDIENTE = 'PEND', 'Pendiente'
        COMPLETADO = 'COMP', 'Completado'   
        FALLIDO = 'FAIL', 'Fallido'
        REEMBOLSADO = 'REEM', 'Reembolsado'

    clase_agendada = models.OneToOneField(
        ClasesAgendadas, 
        on_delete=models.CASCADE,
        related_name='comprobante'
    )

    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(
        max_length=4,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDIENTE
    )

    def __str__(self):
        return f"Pago de {self.total} para {self.clase_agendada}"