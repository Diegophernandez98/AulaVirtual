from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import hashlib
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Importar Modelos
from .models import Usuario, ClasesAgendadas, ComprobantePago, Asignatura, Disponibilidad, TipoUsuario

# Importar Formularios
from .forms import RegistroUsuarioForm, AgendarClaseForm, DisponibilidadForm



# --- VISTAS PÚBLICAS ---

def home(request):
    return render(request, "home.html")

def nosotros(request):
    return render(request, "nosotros.html")

@login_required
def buscarProfesor(request):
    # Trasladamos la lógica de búsqueda que estaba en panel_estudiante hacia aquí
    profesores = Usuario.objects.filter(tipo_usuario__nombre__icontains='Profesor')

    query = request.GET.get('q')      
    filtro = request.GET.get('filtro')  

    if query:
        if filtro == 'asignatura':
            profesores = profesores.filter(asignaturas__nombre__icontains=query).distinct()
        else:
            profesores = profesores.filter(
                Q(nombre__icontains=query) | 
                Q(apellido__icontains=query)
            )

    context = {
        'profesores': profesores, 
    }
    # Asegúrate de tener un archivo HTML llamado 'buscarProfesor.html' 
    # y pega allí el código de la tarjeta de búsqueda y lista de profesores que quitaste.
    return render(request, "buscarProfesor.html", context)

# --- VISTAS DE AUTENTICACIÓN ---

def registro(request):
    if request.method == 'POST':
        # Instanciamos el formulario con los datos recibidos
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            # Obtenemos los datos limpios y validados
            data = form.cleaned_data
            
            try:
                # Obtenemos el objeto TipoUsuario seleccionado en el formulario
                # data.get('tipo_usuario') devuelve el objeto modelo directamente gracias a ModelChoiceField
                tipo_usuario_obj = data.get('tipo_usuario')
                
                # Creamos el usuario usando el método personalizado create_user del Manager
                # Este método se encarga de hashear la contraseña correctamente
                nuevo_usuario = Usuario.objects.create_user(
                    username=data.get('username'),
                    password=data.get('password'), 
                    nombre=data.get('nombre'),
                    apellido=data.get('apellido'),
                    email=data.get('email'),
                    tipo_usuario=tipo_usuario_obj
                )
                
                # Mensaje de éxito para mostrar en el login
                messages.success(request, '¡Te has registrado exitosamente! Ya puedes iniciar sesión.')
                
                # Redirección inmediata al login para evitar reenvíos del formulario
                return redirect('login') 

            except Exception as e:
                # Capturamos cualquier error inesperado durante la creación (ej. base de datos caída)
                messages.error(request, f'Ha ocurrido un error inesperado al crear tu cuenta: {e}')
        else:
            # Si el formulario no es válido, los errores se mostrarán automáticamente en el HTML
            # gracias a {% if form.errors %} que agregamos antes.
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Si es una petición GET, mostramos el formulario vacío
        form = RegistroUsuarioForm()

    return render(request, 'registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # 1. Obtener datos del formulario
        usuario_nombre = request.POST.get('username')
        contrasena = request.POST.get('password')
        rol_seleccionado = request.POST.get('role') # 'estudiante', 'profesor', 'admin'
        # 2. Autenticar credenciales básicas (Usuario y Contraseña)
        user = authenticate(request, username=usuario_nombre, password=contrasena)
        
        if user is not None:
            # 3. VERIFICACIÓN DE ROL (Nueva Lógica)
            # Obtenemos el nombre del rol desde la base de datos
            # Asumimos que user.tipo_usuario.nombre puede ser 'Estudiante', 'Docente', 'Administrador'
            # Convertimos a minúsculas (.lower()) para comparar sin problemas ('Docente' vs 'docente')
            
            rol_real_db = user.tipo_usuario.nombre.lower() if user.tipo_usuario else ''
            print(f"rol real: {rol_real_db}")
            print(f"Rol seleccionado: {rol_seleccionado}")
            # Mapeo simple: Lo que dice el select HTML vs Lo que dice la Base de Datos
            # HTML value : Base de Datos value (normalizado a minúscula)
            es_rol_valido = False

            if rol_seleccionado == 'profesor' and (rol_real_db == 'docente' or rol_real_db == 'profesor'):
                es_rol_valido = True
            elif rol_seleccionado == 'estudiante' and rol_real_db == 'estudiante':
                es_rol_valido = True
            elif rol_seleccionado == 'admin' and (user.is_superuser or user.is_staff):
                es_rol_valido = True # Los admin suelen validarse por is_superuser, no solo por tipo_usuario
            
            if es_rol_valido:
                # 4. Si todo coincide, iniciamos la sesión
                login(request, user)
                
                # 5. Redirección
                if rol_seleccionado == 'profesor':
                    return redirect('docente') 
                elif rol_seleccionado == 'estudiante':
                    return redirect('estudiante')
                elif rol_seleccionado == 'admin':
                    return redirect('admin') # Asegúrate que esta URL exista en urls.py
                else:
                    return redirect('home')
            else:
                # 6. Error de Rol: El usuario existe pero eligió el rol incorrecto
                messages.error(request, f"Tu cuenta no tiene permisos de {rol_seleccionado.capitalize()}.")
        
        else:
            # 7. Error de Credenciales
            messages.error(request, "Usuario o contraseña incorrectos")
    
    return render(request, 'login.html')




# --- PANELES PRINCIPALES ---
@login_required
def panel_estudiante(request):
    if request.user.tipo_usuario.nombre.lower() != 'estudiante':
        return redirect('login')
    
    # 1. Obtenemos el tiempo actual
    ahora = timezone.now()
    margen_tiempo = ahora - timedelta(minutes=90)

    # 2. Filtramos las próximas clases para que se vean en el panel principal
    clases_proximas = ClasesAgendadas.objects.filter(
        estudiante=request.user,
        fecha__gte=margen_tiempo,
        estado='AGEN',
        oculto_para_estudiante=False # Respetamos el borrado lógico
    ).order_by('fecha')

    # 3. Enviamos las clases al template
    context = {
        'clases_proximas': clases_proximas, 
    }

    return render(request, 'estudiante.html', context)


@login_required
def panel_docente(request):
    # 1. Seguridad
    rol = request.user.tipo_usuario.nombre.lower() if request.user.tipo_usuario else ''
    if rol not in ['docente', 'profesor']:
        return redirect('home')

    # 2. Fechas de referencia
    now = timezone.localtime(timezone.now())
    hoy = now.date()
    manana = hoy + timedelta(days=1)
    
    # Margen de tiempo para considerar una clase como "Próxima" (igual que en mis_clases_agendadas)
    margen_tiempo = now - timedelta(minutes=90)

    # 3. Obtener todas las clases futuras (Para la tabla principal)
    clases_proximas = ClasesAgendadas.objects.filter(
        docente=request.user,
        fecha__gte=margen_tiempo, # Usamos el margen de 90 min
        estado='AGEN'
    ).order_by('fecha')

    # 4. Agrupar las clases en listas separadas para el Resumen (Hoy/Mañana)
    clases_hoy = []
    clases_manana = []

    for clase in clases_proximas: # Iteramos sobre la lista ya filtrada
        fecha_clase = timezone.localtime(clase.fecha).date() # Aseguramos que sea hora local
        
        if fecha_clase == hoy:
            clases_hoy.append(clase)
        elif fecha_clase == manana:
            clases_manana.append(clase)

    # 5. Contexto para el template
    context = {
        'clases_proximas': clases_proximas, # <- NUEVO: Toda la lista para la tabla
        'clases_hoy': clases_hoy,
        'clases_manana': clases_manana,
        'now': now,
        'es_docente': True # <- NUEVO: Para reutilizar el HTML de botones
    }

    return render(request, "docente.html", context)



@csrf_exempt # Permitimos POST sin token CSRF para facilitar el fetch desde JS (en producción usar token)
def guardar_pizarra(request, clase_id):
    if request.method == 'POST':
        try:
            # 1. Obtener la clase
            clase = ClasesAgendadas.objects.get(id=clase_id)
            
            # 2. Leer los datos JSON que envía el frontend
            data = json.loads(request.body)
            elements = data.get('elements')
            
            # 3. Guardar en la base de datos como texto
            clase.datos_pizarra = json.dumps(elements)
            clase.save()
            
            return JsonResponse({'status': 'ok', 'mensaje': 'Pizarra guardada'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'msg': 'Método no permitido'}, status=405)

# --- SALA VIRTUAL (ACTUALIZADO) ---

@login_required
def sala(request, clase_id):
    # 1. Obtener la clase
    clase = get_object_or_404(ClasesAgendadas, id=clase_id)

    # 2. Seguridad
    es_estudiante = (request.user == clase.estudiante)
    es_docente = (request.user == clase.docente)

    if not es_estudiante and not es_docente and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para entrar a esta sala.")
        return redirect('mis_clases_agendadas')

    # 3. Generar ID Seguro para la sala
    cadena_unica = f"CLASE-{clase.id}-{settings.SECRET_KEY}"
    room_uuid = hashlib.sha256(cadena_unica.encode()).hexdigest()[:10]

    # 4. Contexto (Datos para el HTML)
    context = {
        'clase': clase,
        'nombre_usuario': request.user.nombre,
        'rol': 'Profesor' if es_docente else 'Estudiante',
        'room_id': room_uuid,
        # Pasamos el ID real para que la API sepa dónde guardar
        'clase_id_real': clase.id,
        # Pasamos los datos guardados (o lista vacía si es nueva)
        'datos_pizarra_inicial': clase.datos_pizarra if clase.datos_pizarra else "[]"
    }
    return render(request, "sala.html", context)






# --- VISTAS PROTEGIDAS (REQUIEREN LOGIN) ---

@login_required
def portalPagos(request):
    return render(request, "portalPagos.html")



# --- GESTIÓN DE HORARIOS ---
@login_required
def gestionar_horario(request):
    if request.user.tipo_usuario.nombre not in ['Docente', 'Profesor']:
        return redirect('home') 

    # --- CORRECCIÓN AQUÍ ---
    # 1. Obtenemos la fecha REAL en Chile (Local), no la UTC
    ahora_local = timezone.localtime(timezone.now())
    hoy_chile = ahora_local.date()

    # 2. Borramos solo lo que sea ANTERIOR a hoy (hora Chile)
    Disponibilidad.objects.filter(docente=request.user, fecha__lt=hoy_chile).delete()
    # -----------------------

    # 3. Obtener horarios
    horarios = Disponibilidad.objects.filter(docente=request.user).order_by('fecha', 'hora_inicio')

    # 4. Procesar Formulario
    if request.method == 'POST':
        form = DisponibilidadForm(request.POST)
        if form.is_valid():
            nuevo_horario = form.save(commit=False)
            nuevo_horario.docente = request.user 
            
            # ASIGNAR LA FECHA CALCULADA (Día/Mes + Año Inteligente)
            # Esta viene del forms.py que modificamos en el paso anterior
            nuevo_horario.fecha = form.cleaned_data['fecha_calculada']
            
            nuevo_horario.save()
            messages.success(request, '¡Hora disponible creada correctamente!')
            # Redirigimos a la misma vista para limpiar el formulario y recargar la tabla
            return redirect('gestionar_horario')
        else:
            messages.error(request, 'Error en el formulario. Revisa los datos.')
    else:
        # Pre-seleccionar el mes actual
        form = DisponibilidadForm(initial={'mes': timezone.now().month})

    # 5. Enviar todo al HTML
    return render(request, 'gestionar_horario.html', {
        'form': form, 
        'horarios': horarios # <--- ESTO ES LO QUE HACE QUE APAREZCAN ABAJO
    })




@login_required
def eliminar_horario(request, id):
    # Buscamos el horario específico por su ID
    # get_object_or_404 es seguro: si el ID no existe o no es de este profe, da error 404
    horario = get_object_or_404(Disponibilidad, id=id, docente=request.user)
    
    # Lo borramos de la base de datos
    horario.delete()
    
    messages.success(request, 'Horario eliminado.')
    return redirect('gestionar_horario')




@login_required
def mis_clases_agendadas(request):
    usuario_actual = request.user
    rol_nombre = usuario_actual.tipo_usuario.nombre.lower() if usuario_actual.tipo_usuario else ''
    
    # NUEVO: Filtramos para que solo traiga las que NO están ocultas para este usuario
    if rol_nombre == 'estudiante':
            clases_del_usuario = ClasesAgendadas.objects.filter(
                estudiante=usuario_actual
            ).exclude(oculto_para_estudiante=True) # <-- Excluir donde sea True explícitamente
    else:
        clases_del_usuario = ClasesAgendadas.objects.filter(
            docente=usuario_actual
        ).exclude(oculto_para_docente=True) # <-- Excluir donde sea True explícitamente

    ahora = timezone.now()
    margen_tiempo = ahora - timedelta(minutes=90)

    # Filtramos usando este margen (esto se mantiene igual)
    clases_proximas = clases_del_usuario.filter(fecha__gte=margen_tiempo).order_by('fecha')
    clases_pasadas = clases_del_usuario.filter(fecha__lt=margen_tiempo).order_by('-fecha')

    clases = {
        'clases_proximas': clases_proximas,
        'clases_pasadas': clases_pasadas,
        'es_docente': (rol_nombre == 'docente' or rol_nombre == 'profesor') 
    }
    return render(request, 'mis_clases_agendadas.html', clases)



@login_required
def editarMiCuenta(request, id):
    # Verificar que el usuario solo edite su propia cuenta
    if request.user.id != int(id) and not request.user.is_superuser:
        return redirect('home')

    usuario = Usuario.objects.get(id=id)
    if request.method == 'GET':
        formulario = RegistroUsuarioForm(instance=usuario)
        return render(request, 'editarMiCuenta.html', {"form": formulario, "id": id})
    elif request.method == 'POST':
        formulario = RegistroUsuarioForm(request.POST, instance=usuario)
        if formulario.is_valid():
            formulario.save()
            return redirect('home') # O donde prefieras
        return render(request, 'editarMiCuenta.html', {"form": formulario, "id": id})

# --- VISTAS ADMIN ---
def listaPagosAdmin(request):
    lista_pagos = ComprobantePago.objects.all()
    return render(request, "listaPagosAdmin.html", {"Pagos": lista_pagos})

def clasesAgendadasAdmin(request):
    agenda = ClasesAgendadas.objects.all()
    return render(request, 'clasesAgendadasAdmin.html', {"agenda": agenda})

def eliminarUsuarios(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    usuario.delete()
    return redirect('home') 

def eliminarAgendamiento(request, id):
    clase = get_object_or_404(ClasesAgendadas, id=id)
    clase.delete()
    return redirect('clasesAgendadasAdmin')

def editarAgendamiento(request,id):
    clasesAgendadas = ClasesAgendadas.objects.get(id=id)
    if request.method == 'GET':
        formulario = AgendarClaseForm(instance=clasesAgendadas)
        return render(request, 'editarAgendamiento.html',  {"form":formulario, "id": id})
    elif request.method == 'POST':
        formulario = AgendarClaseForm(request.POST, instance=clasesAgendadas)
        if formulario.is_valid():
            formulario.save()
        return redirect('clasesAgendadasAdmin')

def editarUsuarios(request, id):
    usuario = Usuario.objects.get(id=id)
    if request.method == 'GET':
        formulario = RegistroUsuarioForm(instance=usuario)
        return render(request, 'editarUsuarios.html', {"form": formulario, "id": id})
    elif request.method == 'POST':
        formulario = RegistroUsuarioForm(request.POST, instance=usuario)
        if formulario.is_valid():
            formulario.save()
        return redirect('listaUsuarios')
    




@login_required
def editarAgendamiento(request,id):
    clasesAgendadas = ClasesAgendadas.objects.get(id=id)
    if request.method == 'GET':
        formulario = AgendarClaseForm(instance=clasesAgendadas)
        return render(request, 'editarAgendamiento.html',  {"form":formulario, "id": id})
    elif request.method == 'POST':
        formulario = AgendarClaseForm(request.POST, instance=clasesAgendadas)
        if formulario.is_valid():
            formulario.save()
        return redirect('clasesAgendadasAdmin')
    



# En views.py
# En views.py

def perfil_profesor(request, id):
    profesor = get_object_or_404(Usuario, id=id)
    
    # --- CORRECCIÓN 1: Usar hora local (Chile) ---
    # Esto asegura que si son las 23:47, siga siendo "hoy" y no "mañana"
    ahora_local = timezone.localtime(timezone.now())
    hoy_local = ahora_local.date()
    hora_actual = ahora_local.time()
    
    # 1. Obtener disponibilidad base (Usando la fecha local)
    todos_horarios = Disponibilidad.objects.filter(
        docente=profesor,
        fecha__gte=hoy_local 
    ).order_by('fecha', 'hora_inicio')
    
    # 2. Buscar clases YA agendadas (Usamos ahora_local para consistencia)
    clases_ocupadas = ClasesAgendadas.objects.filter(
        docente=profesor,
        fecha__gte=ahora_local, 
        estado='AGEN'    
    )
    
    # 3. MAPA DE OCUPACIÓN
    ocupados_set = set()
    for clase in clases_ocupadas:
        fecha_local = timezone.localtime(clase.fecha)
        ocupados_set.add((fecha_local.date(), fecha_local.time()))
    
    # 4. Clasificar y Filtrar
    horarios_disponibles = []
    horarios_ocupados = []

    for h in todos_horarios:
        # A) Si el horario está en el set de ocupados
        if (h.fecha, h.hora_inicio) in ocupados_set:
            horarios_ocupados.append(h)
        else:
            # --- CORRECCIÓN 2: Ocultar horas pasadas del día de hoy ---
            # Si la fecha es hoy, pero la hora ya pasó (ej: son 23:47 y el bloque era 23:30)
            if h.fecha == hoy_local and h.hora_inicio < hora_actual:
                continue # Saltamos este ciclo, no lo mostramos
            
            # Si pasa la validación, lo agregamos
            horarios_disponibles.append(h)
    
    context = {
        'profesor': profesor,
        'horarios_disponibles': horarios_disponibles,
        'horarios_ocupados': horarios_ocupados
    }
    return render(request, 'perfil_profesor.html', context)




@login_required
def confirmar_reserva(request, horario_id):
    if request.method != 'POST':
        return redirect('home')

    horario_base = get_object_or_404(Disponibilidad, id=horario_id)
    
    # LÓGICA NUEVA: Usamos la fecha exacta del horario disponible
    fecha_clase = horario_base.fecha 
    
    # Crear objeto datetime con zona horaria
    try:
        fecha_hora_final = timezone.make_aware(
            datetime.combine(fecha_clase, horario_base.hora_inicio)
        )
    except Exception:
        fecha_hora_final = datetime.combine(fecha_clase, horario_base.hora_inicio)

    # Validar que no se intente reservar algo que ya pasó (por seguridad extra)
    if fecha_hora_final < timezone.now():
        messages.error(request, "Este horario ya ha expirado.")
        return redirect('perfil_profesor', id=horario_base.docente.id)

    # Asignatura
    asignatura_clase = horario_base.docente.asignaturas.first()
    if not asignatura_clase:
        asignatura_clase, created = Asignatura.objects.get_or_create(nombre="Clase Particular")

    # CREAR LA RESERVA (AQUÍ ESTÁ EL CAMBIO)
    ClasesAgendadas.objects.create(
        fecha=fecha_hora_final,
        costo=15000, 
        asignatura=asignatura_clase,
        estudiante=request.user,
        docente=horario_base.docente,
        estado='AGEN',
        # Aseguramos que los campos de borrado lógico inicien en False
        oculto_para_estudiante=False, 
        oculto_para_docente=False
    )

    
    
    messages.success(request, "¡Clase reservada exitosamente para el " + str(fecha_clase) + "!")
    return redirect('perfil_profesor', id=horario_base.docente.id)



@login_required
def cancelar_clase(request, clase_id):
    clase = get_object_or_404(ClasesAgendadas, id=clase_id)

    # SEGURIDAD: Solo el estudiante o el docente de esa clase pueden modificarla
    if request.user != clase.estudiante and request.user != clase.docente:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('mis_clases_agendadas')

    # LÓGICA DE BORRADO
    if clase.fecha < timezone.now():
        # 1. Es una clase pasada (Historial): Hacemos un BORRADO LÓGICO (Ocultar)
        if request.user == clase.estudiante:
            clase.oculto_para_estudiante = True
            messages.success(request, "Registro eliminado de tu historial.")
        elif request.user == clase.docente:
            clase.oculto_para_docente = True
            messages.success(request, "Registro eliminado de tu historial.")
        
        clase.save() # Guardamos los cambios en lugar de usar .delete()

    else:
        # 2. Es una clase futura: Hacemos un BORRADO FÍSICO (Cancelar de verdad)
        clase.delete()
        messages.success(request, "La clase ha sido cancelada exitosamente.")

    # Redirección para devolver al usuario a la página donde estaba
    referer = request.META.get('HTTP_REFERER')
    if referer and 'mis_clases_agendadas' in referer:
         return redirect('mis_clases_agendadas')
    elif request.user.tipo_usuario.nombre.lower() in ['docente', 'profesor']:
         return redirect('docente')
    else:
         return redirect('estudiante')