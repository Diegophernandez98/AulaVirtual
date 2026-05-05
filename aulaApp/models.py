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

# --- MODELOS DE NEGOCIO ---

class ClasesAgendadas(models.Model):
    # Opciones para estados de la clase
    class EstadoClase(models.TextChoices):
        AGENDADA = 'AGEN', 'Agendada'
        COMPLETADA = 'COMP', 'Completada'
        CANCELADA = 'CANC', 'Cancelada'

    fecha = models.DateTimeField()
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)

    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE, 
            related_name='clases_como_estudiante', 
            limit_choices_to={'tipo_usuario__id': 1})
    
    docente = models.ForeignKey(Usuario, on_delete=models.CASCADE, 
            related_name='clases_como_docente', 
            limit_choices_to={'tipo_usuario__id': 2})
    
    estado = models.CharField(
        max_length=4,
        choices=EstadoClase.choices,
        default=EstadoClase.AGENDADA
    )


    # Guardará el JSON de Excalidraw como texto.
    # default="[]" asegura que empiece como una pizarra vacía válida.
    datos_pizarra = models.TextField(blank=True, null=True, default="[]")

    def __str__(self):
        return f"Clase de {self.asignatura.nombre} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"
    
    
    # NUEVOS CAMPOS PARA EL BORRADO LÓGICO EN EL HISTORIAL
    oculto_para_estudiante = models.BooleanField(default=False)
    oculto_para_docente = models.BooleanField(default=False)




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
    
