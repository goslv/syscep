from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, datetime
import json
from django.db.models import Max
from .models import Sede, Alumno, Funcionario, Pago, Carrera, AsistenciaFuncionario, Materia, Egreso, CanjeEstrellas, SolicitudEliminacion
from .forms import PagoForm, AlumnoForm, FuncionarioForm, AsistenciaForm, SedeForm, CarreraForm, UsuarioForm, \
    MateriaForm, EgresoForm, PerfilForm
from .decorators import admin_required


# VISTAS DE AUTENTICACIÓN

def login_view(request):
    """Vista de login personalizada"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        # Crea el usuario
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('login')
    return render(request, 'registrar.html')

#Dashboard

@login_required
def dashboard(request):
    hoy = timezone.now().date()
    # Estadísticas generales
    total_alumnos = Alumno.objects.filter(activo=True).count()
    total_funcionarios = Funcionario.objects.filter(activo=True).count()
    total_carreras = Carrera.objects.filter(activa=True).count()
    total_sedes = Sede.objects.filter(activa=True).count()

    # Pagos del día
    pagos_hoy = Pago.objects.filter(fecha=hoy)
    ingresos_hoy = pagos_hoy.aggregate(Sum('importe_total'))['importe_total__sum'] or 0

    # Estado de pagos de alumnos
    alumnos_activos = Alumno.objects.filter(activo=True)
    alumnos_al_dia = sum(1 for a in alumnos_activos if a.estado_pagos == 'AL_DIA')
    alumnos_por_vencer = sum(1 for a in alumnos_activos if a.estado_pagos == 'CERCANO_VENCIMIENTO')
    alumnos_atrasados = sum(1 for a in alumnos_activos if a.estado_pagos == 'ATRASADO')

    # Pagos recientes
    pagos_recientes = Pago.objects.select_related('alumno', 'sede', 'carrera').order_by('-fecha_creacion')[:10]

    context = {
        'total_alumnos': total_alumnos,
        'total_funcionarios': total_funcionarios,
        'total_carreras': total_carreras,
        'total_sedes': total_sedes,
        'ingresos_hoy': ingresos_hoy,
        'cantidad_pagos_hoy': pagos_hoy.count(),
        'alumnos_al_dia': alumnos_al_dia,
        'alumnos_por_vencer': alumnos_por_vencer,
        'alumnos_atrasados': alumnos_atrasados,
        'pagos_recientes': pagos_recientes,
    }

    return render(request, 'inicio.html', context)

#Alumnos

@login_required
def lista_alumnos(request):
    alumnos = Alumno.objects.filter(activo=True).select_related('carrera', 'sede')
    # Filtros
    sede_id = request.GET.get('sede')
    carrera_id = request.GET.get('carrera')
    estado = request.GET.get('estado')
    busqueda = request.GET.get('busqueda')

    if sede_id:
        alumnos = alumnos.filter(sede_id=sede_id)
    if carrera_id:
        alumnos = alumnos.filter(carrera_id=carrera_id)
    if busqueda:
        alumnos = alumnos.filter(
            Q(nombre__icontains=busqueda) |
            Q(apellido__icontains=busqueda) |
            Q(cedula__icontains=busqueda)
        )

    # Aplicar filtro de estado
    alumnos_list = list(alumnos)
    if estado:
        alumnos_list = [a for a in alumnos_list if a.estado_pagos == estado]

    context = {
        'alumnos': alumnos_list,
        'sedes': Sede.objects.filter(activa=True),
        'carreras': Carrera.objects.filter(activa=True),
        'filtros': {
            'sede': sede_id,
            'carrera': carrera_id,
            'estado': estado,
            'busqueda': busqueda,
        }
    }
    return render(request, 'alumnos/listaAlumnos.html', context)

@login_required
def detalle_alumno(request, alumno_uuid):
    """Detalle de un alumno con historial de pagos"""
    alumno = get_object_or_404(Alumno, uuid=alumno_uuid)
    pagos = alumno.pagos.all().order_by('-fecha')

    context = {
        'alumno': alumno,
        'pagos': pagos,
        'total_pagado': pagos.aggregate(Sum('importe_total'))['importe_total__sum'] or 0,
        'puede_rendir': alumno.puede_rendir_examen,
        'total_estrellas': alumno.total_estrellas,
        'canjes': alumno.canjes.all().order_by('-fecha'),
    }

    return render(request, 'alumnos/detalleAlumnos.html', context)


@login_required
def canjear_estrellas(request, alumno_uuid):
    """Registrar un canje de estrellas para un alumno"""
    if request.method == 'POST':
        alumno = get_object_or_404(Alumno, uuid=alumno_uuid)
        cantidad = int(request.POST.get('cantidad', 0))
        concepto = request.POST.get('concepto', '').strip()

        if cantidad <= 0:
            messages.error(request, 'La cantidad de estrellas debe ser mayor a cero.')
        elif cantidad > alumno.total_estrellas:
            messages.error(request, 'El alumno no tiene suficientes estrellas para este canje.')
        elif not concepto:
            messages.error(request, 'Debe especificar el concepto del canje.')
        else:
            CanjeEstrellas.objects.create(
                alumno=alumno,
                cantidad=cantidad,
                concepto=concepto,
                usuario_registro=request.user
            )
            messages.success(request, f'Se han canjeado {cantidad} estrellas exitosamente.')
            
    return redirect('detalle_alumno', alumno_uuid=alumno_uuid)


@login_required
def crear_alumno(request):
    """Crear un nuevo alumno"""
    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            alumno = form.save()
            messages.success(request, f'Alumno {alumno.nombre} {alumno.apellido} registrado exitosamente.')
            return redirect('detalle_alumno', alumno_uuid=alumno.uuid)
    else:
        form = AlumnoForm()

    return render(request, 'alumnos/formAlumnos.html', {
        'form': form,
        'titulo': 'Registrar Nuevo Alumno',
        'boton': 'Registrar Alumno'
    })


@login_required
def editar_alumno(request, alumno_uuid):
    """Editar un alumno existente"""
    alumno = get_object_or_404(Alumno, uuid=alumno_uuid)
    if request.method == 'POST':
        form = AlumnoForm(request.POST, instance=alumno)
        if form.is_valid():
            form.save()
            messages.success(request, f'Alumno {alumno.nombre} {alumno.apellido} actualizado exitosamente.')
            return redirect('detalle_alumno', alumno_uuid=alumno.uuid)
    else:
        form = AlumnoForm(instance=alumno)

    return render(request, 'alumnos/formAlumnos.html', {
        'form': form,
        'alumno': alumno,
        'titulo': f'Editar Alumno: {alumno.nombre_completo}',
        'boton': 'Guardar Cambios'
    })

# Vista adicional para búsqueda de alumnos (útil para AJAX en el formulario)
@login_required
def buscar_alumno(request):
    """Vista para buscar alumnos (util para autocompletado)"""
    from django.http import JsonResponse

    query = request.GET.get('q', '').strip()
    if len(query) >= 2:
        alumnos = Alumno.objects.select_related('sede', 'carrera').filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(cedula__icontains=query)
        )[:10]

        resultados = [{
            'id': alumno.id,
            'nombre_completo': alumno.nombre_completo,
            'cedula': alumno.cedula,
            'sede_id': alumno.sede_id,
            'sede': alumno.sede.nombre if alumno.sede else '',
            'carrera_id': alumno.carrera_id,
            'carrera': alumno.carrera.nombre if alumno.carrera else '',
            'monto_mensualidad': str(alumno.carrera.monto_mensualidad) if alumno.carrera else ''
        } for alumno in alumnos]

        return JsonResponse({'resultados': resultados})

    return JsonResponse({'resultados': []})
#Pagos

@login_required
@admin_required
def lista_pagos(request):
    pagos = Pago.objects.all().select_related('alumno', 'sede', 'carrera').order_by('-fecha', '-id')

    # Filtros
    sede_id = request.GET.get('sede')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if sede_id:
        pagos = pagos.filter(sede_id=sede_id)

    if fecha_desde:
        pagos = pagos.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        pagos = pagos.filter(fecha__lte=fecha_hasta)

    # Limitar a 100 registros
    pagos = pagos[:100]

    # Obtener todas las sedes para el filtro
    sedes = Sede.objects.all().order_by('nombre')

    context = {
        'pagos': pagos,
        'sedes': sedes,
    }

    return render(request, 'pagos/listaPagos.html', context)


@login_required
def detalle_pago(request, pago_uuid):
    """Vista para ver el detalle completo de un pago"""
    pago = get_object_or_404(Pago.objects.select_related('alumno', 'sede', 'carrera'), uuid=pago_uuid)

    context = {
        'pago': pago,
    }

    return render(request, 'pagos/detallePago.html', context)


@login_required
def registrar_pago(request):
    """Vista para registrar un nuevo pago"""
    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES)
        if form.is_valid():
            pago = form.save(commit=False)

            # Asignar usuario que registra
            pago.usuario_registro = request.user

            es_cliente_diferenciado = form.cleaned_data.get('es_cliente_diferenciado')
            if not pago.numero_recibo:
                pago.numero_recibo = None

            pago.nombre_cliente = form.cleaned_data.get('nombre_cliente') if es_cliente_diferenciado else None
            pago.alumno = None if es_cliente_diferenciado else form.cleaned_data.get('alumno')
            pago.carrera = form.cleaned_data.get('carrera') or (pago.alumno.carrera if pago.alumno else None)
            pago.validez_pago = form.cleaned_data.get('validez_pago')
            pago.fecha_vencimiento = form.cleaned_data.get('fecha_vencimiento')
            pago.curso = form.cleaned_data.get('curso')
            pago.monto_unitario = form.cleaned_data.get('monto_unitario')
            pago.cantidad_cuotas = form.cleaned_data.get('cantidad_cuotas') or 1
            pago.estrellas = form.cleaned_data.get('estrellas') or 0
            pago.save()
            if pago.numero_recibo:
                messages.success(request, f'Pago registrado exitosamente. Recibo No. {pago.numero_recibo}')
            else:
                messages.success(request, 'Pago registrado exitosamente.')
            return redirect('detalle_pago', pago_uuid=pago.uuid)
    else:
        form = PagoForm()

    context = {
        'form': form,
        'titulo': 'Registrar Pago',
        'boton': 'Registrar',
        'carreras_data': json.dumps(
            list(Carrera.objects.values('id', 'monto_mensualidad')),
            default=str
        ),
    }

    return render(request, 'pagos/formPagos.html', context)


@login_required
@admin_required
def editar_pago(request, pago_uuid):
    """Vista para editar un pago existente"""
    pago = get_object_or_404(Pago, uuid=pago_uuid)

    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES, instance=pago)
        if form.is_valid():
            pago = form.save(commit=False)

            es_cliente_diferenciado = form.cleaned_data.get('es_cliente_diferenciado')
            if not pago.numero_recibo:
                pago.numero_recibo = None

            pago.nombre_cliente = form.cleaned_data.get('nombre_cliente') if es_cliente_diferenciado else None
            pago.alumno = None if es_cliente_diferenciado else form.cleaned_data.get('alumno')
            pago.carrera = form.cleaned_data.get('carrera') or (pago.alumno.carrera if pago.alumno else None)
            pago.validez_pago = form.cleaned_data.get('validez_pago')
            pago.fecha_vencimiento = form.cleaned_data.get('fecha_vencimiento')
            pago.curso = form.cleaned_data.get('curso')
            pago.monto_unitario = form.cleaned_data.get('monto_unitario')
            pago.cantidad_cuotas = form.cleaned_data.get('cantidad_cuotas') or 1
            pago.estrellas = form.cleaned_data.get('estrellas') or 0
            pago.save()
            if pago.numero_recibo:
                messages.success(request, f'Pago actualizado exitosamente. Recibo No. {pago.numero_recibo}')
            else:
                messages.success(request, 'Pago actualizado exitosamente.')
            return redirect('detalle_pago', pago_uuid=pago.uuid)
    else:
        form = PagoForm(instance=pago)

    context = {
        'form': form,
        'pago': pago,
        'titulo': 'Editar Pago',
        'boton': 'Actualizar',
        'carreras_data': json.dumps(
            list(Carrera.objects.values('id', 'monto_mensualidad')),
            default=str
        ),
    }

    return render(request, 'pagos/formPagos.html', context)


@login_required
@admin_required
def eliminar_pago(request, pago_uuid):
    """Vista para eliminar un pago o solicitar su eliminación"""
    pago = get_object_or_404(Pago, uuid=pago_uuid)

    if request.method == 'POST':
        if request.user.is_staff:
            numero_recibo = pago.numero_recibo
            pago.delete()
            if numero_recibo:
                messages.success(request, f'Pago con recibo No. {numero_recibo} eliminado exitosamente.')
            else:
                messages.success(request, 'Pago sin recibo eliminado exitosamente.')
            return redirect('lista_pagos')
        else:
            motivo = request.POST.get('motivo', 'No especificado')
            datos = {
                'numero_recibo': pago.numero_recibo,
                'pagador': pago.nombre_pagador,
                'monto': str(pago.importe_total),
                'fecha': str(pago.fecha)
            }
            SolicitudEliminacion.objects.create(
                usuario_solicita=request.user,
                modelo='PAGO',
                objeto_id=pago.id,
                motivo=motivo,
                datos_objeto=datos
            )
            messages.info(request, 'Solicitud de eliminación enviada al administrador.')
            return redirect('detalle_pago', pago_uuid=pago.uuid)

    # Si no es POST, redirigir a la lista
    return redirect('lista_pagos')

# VISTAS DE FUNCIONARIOS

@login_required
@admin_required
def lista_funcionarios(request):
    funcionarios = Funcionario.objects.filter(activo=True).select_related('sede')

    # Filtros
    cargo = request.GET.get('cargo')
    sede_id = request.GET.get('sede')

    if cargo:
        funcionarios = funcionarios.filter(cargo=cargo)
    if sede_id:
        funcionarios = funcionarios.filter(sede_id=sede_id)

    context = {
        'funcionarios': funcionarios,
        'sedes': Sede.objects.filter(activa=True),
        'cargos': Funcionario.CARGO_CHOICES,
    }

    return render(request, 'funcionarios/listaFuncionarios.html', context)


@login_required
@admin_required
def crear_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            funcionario = form.save()
            messages.success(request, f'Funcionario {funcionario.nombre_completo} registrado exitosamente.')
            return redirect('lista_funcionarios')
    else:
        form = FuncionarioForm()

    return render(request, 'funcionarios/formFuncionario.html', {
        'form': form,
        'titulo': 'Registrar Nuevo Funcionario',
        'boton': 'Registrar Funcionario'
    })


@login_required
@admin_required
def registrar_asistencia(request):
    """Registrar asistencia de funcionarios"""
    if request.method == 'POST':
        form = AsistenciaForm(request.POST)
        if form.is_valid():
            asistencia = form.save()
            estado = "Presente" if asistencia.presente else "Ausente"
            messages.success(request, f'Asistencia registrada: {asistencia.funcionario.nombre_completo} - {estado}')
            return redirect('lista_asistencias')
    else:
        # Pre-cargar la fecha de hoy
        form = AsistenciaForm(initial={'fecha': timezone.now().date(), 'presente': True})

    return render(request, 'funcionarios/formAsistencia.html', {
        'form': form,
        'titulo': 'Registrar Asistencia',
        'boton': 'Registrar Asistencia'
    })


@login_required
@admin_required
def lista_asistencias(request):
    """Lista de asistencias"""
    asistencias = AsistenciaFuncionario.objects.all().select_related('funcionario').order_by('-fecha')

    # Filtros
    fecha = request.GET.get('fecha')
    funcionario_id = request.GET.get('funcionario')

    if fecha:
        asistencias = asistencias.filter(fecha=fecha)
    if funcionario_id:
        asistencias = asistencias.filter(funcionario_id=funcionario_id)

    # Limitar a 50
    asistencias = asistencias[:50]

    context = {
        'asistencias': asistencias,
        'funcionarios': Funcionario.objects.filter(activo=True),
    }

    return render(request, 'funcionarios/listaAsistencias.html', context)

# VISTAS DE SEDES

@login_required
@admin_required
def lista_sedes(request):
    """Lista de todas las sedes con rendición del día"""
    sedes = Sede.objects.filter(activa=True)
    hoy = timezone.now().date()

    sedes_data = []
    for sede in sedes:
        rendicion = sede.rendicion_dia(hoy)
        sedes_data.append({
            'sede': sede,
            'ingresos_hoy': rendicion['total_ingresos'],
        })

    context = {
        'sedes_data': sedes_data,
        'fecha': hoy,
    }

    return render(request, 'sedes/listaSedes.html', context)


@login_required
@admin_required
def rendicion_sede(request, sede_id):
    """Vista de rendición de una sede específica"""
    sede = get_object_or_404(Sede, pk=sede_id)
    fecha_str = request.GET.get('fecha')

    if fecha_str:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    else:
        fecha = timezone.now().date()

    rendicion = sede.rendicion_dia(fecha)

    context = {
        'sede': sede,
        'fecha': fecha,
        'rendicion': rendicion,
        'pagos': rendicion['pagos'].select_related('alumno'),
    }

    return render(request, 'sedes/rendicionSedes.html', context)

@login_required
@admin_required
def crear_sede(request):
    """Crear una nueva sede"""
    if request.method == 'POST':
        form = SedeForm(request.POST)
        if form.is_valid():
            sede = form.save()
            messages.success(request, f'Sede {sede.nombre} creada exitosamente.')
            return redirect('lista_sedes')
    else:
        form = SedeForm()

    return render(request, 'sedes/formSedes.html', {
        'form': form,
        'titulo': 'Crear Nueva Sede',
        'boton': 'Crear Sede'
    })

# VISTAS DE CARRERAS

# Context Processor para notificaciones
def notifications_processor(request):
    if not request.user.is_authenticated:
        return {'examenes_proximos': [], 'total_notificaciones': 0, 'solicitudes_pendientes_count': 0}

    hoy = timezone.now().date()
    en_tres_dias = hoy + timedelta(days=3)

    # Buscar exámenes parciales y finales en el rango de hoy a 3 días
    parciales = Materia.objects.filter(
        fecha_examen_parcial__gte=hoy,
        fecha_examen_parcial__lte=en_tres_dias
    ).select_related('carrera')

    finales = Materia.objects.filter(
        fecha_examen_final__gte=hoy,
        fecha_examen_final__lte=en_tres_dias
    ).select_related('carrera')

    notificaciones = []

    for m in parciales:
        notificaciones.append({
            'tipo': 'Examen Parcial',
            'materia': m.nombre,
            'carrera': m.carrera.nombre,
            'carrera_id': m.carrera.id,
            'fecha': m.fecha_examen_parcial,
            'icon': 'bi-calendar-event',
            'color': 'text-primary'
        })

    for m in finales:
        notificaciones.append({
            'tipo': 'Examen Final',
            'materia': m.nombre,
            'carrera': m.carrera.nombre,
            'carrera_id': m.carrera.id,
            'fecha': m.fecha_examen_final,
            'icon': 'bi-calendar-check',
            'color': 'text-danger'
        })

    # Solicitudes de eliminación pendientes (solo para administradores)
    solicitudes_pendientes = []
    solicitudes_pendientes_count = 0
    if request.user.is_staff:
        solicitudes_pendientes_objs = SolicitudEliminacion.objects.filter(estado='PENDIENTE').select_related('usuario_solicita')
        solicitudes_pendientes_count = solicitudes_pendientes_objs.count()
        for s in solicitudes_pendientes_objs:
            notificaciones.append({
                'id': f'solicitud_{s.id}',
                'tipo': 'Solicitud de Eliminación',
                'materia': f'Solicitado por {s.usuario_solicita.username}',
                'carrera': s.get_modelo_display(),
                'objeto_id': s.objeto_id,
                'motivo': s.motivo,
                'datos_objeto': s.datos_objeto,
                'url_procesar': f'/procesar-solicitud-eliminacion/{s.id}/',
                'fecha': s.fecha_solicitud,
                'icon': 'bi-trash',
                'color': 'text-warning',
                'es_solicitud': True,
                'solicitud_id': s.id
            })

    # Ordenar por fecha
    notificaciones.sort(key=lambda x: x['fecha'].date() if isinstance(x['fecha'], datetime) else x['fecha'])

    return {
        'examenes_proximos': notificaciones,
        'total_notificaciones': len(notificaciones),
        'solicitudes_pendientes_count': solicitudes_pendientes_count
    }


@login_required
def lista_carreras(request):
    carreras = Carrera.objects.filter(activa=True).prefetch_related('materias', 'alumnos')

    # Calcular totales
    total_materias = sum(carrera.materias.count() for carrera in carreras)
    total_docentes = Funcionario.objects.filter(cargo='DOCENCIA', activo=True).count()

    context = {
        'carreras': carreras,
        'total_materias': total_materias,
        'total_docentes': total_docentes,
    }

    return render(request, 'carreras/listaCarreras.html', context)


@login_required
def detalle_carrera(request, carrera_id):
    carrera = get_object_or_404(Carrera, pk=carrera_id)
    materias = carrera.materias.all().select_related('docente')
    docentes = Funcionario.objects.filter(cargo='DOCENCIA', activo=True)

    context = {
        'carrera': carrera,
        'materias': materias,
        'docentes': docentes,
    }

    return render(request, 'carreras/detalleCarrera.html', context)


@login_required
def crear_carrera(request):
    """Crear una nueva carrera"""
    if request.method == 'POST':
        form = CarreraForm(request.POST)
        if form.is_valid():
            carrera = form.save()
            messages.success(request, f'Carrera {carrera.nombre} creada exitosamente.')
            return redirect('detalle_carrera', carrera_id=carrera.id)
    else:
        form = CarreraForm()

    return render(request, 'carreras/formCarreras.html', {
        'form': form,
        'titulo': 'Crear Nueva Carrera',
        'boton': 'Crear Carrera'
    })


@login_required
def crear_materia(request, carrera_id):
    carrera = get_object_or_404(Carrera, pk=carrera_id)

    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            materia = form.save(commit=False)
            materia.carrera = carrera
            materia.save()
            messages.success(request, f'Materia {materia.nombre} agregada exitosamente.')
            return redirect('detalle_carrera', carrera_id=carrera.id)
    else:
        # Pre-cargar el orden siguiente
        ultimo_orden = carrera.materias.aggregate(Max('orden'))['orden__max'] or 0
        form = MateriaForm(initial={'orden': ultimo_orden + 1})

    context = {
        'form': form,
        'carrera': carrera,
        'titulo': f'Agregar Materia a {carrera.nombre}',
        'boton': 'Agregar Materia'
    }

    return render(request, 'carreras/formMaterias.html', context)


@login_required
def editar_materia(request, materia_id):
    materia = get_object_or_404(Materia, pk=materia_id)

    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, f'Materia {materia.nombre} actualizada exitosamente.')
            return redirect('detalle_carrera', carrera_id=materia.carrera.id)
    else:
        form = MateriaForm(instance=materia)

    context = {
        'form': form,
        'materia': materia,
        'carrera': materia.carrera,
        'titulo': f'Editar: {materia.nombre}',
        'boton': 'Guardar Cambios'
    }

    return render(request, 'carreras/formMaterias.html', context)


@login_required
def asignar_docente(request, materia_id):
    materia = get_object_or_404(Materia, pk=materia_id)

    if request.method == 'POST':
        docente_id = request.POST.get('docente_id')
        if docente_id:
            docente = get_object_or_404(Funcionario, pk=docente_id, cargo='DOCENCIA', activo=True)
            materia.docente = docente
            materia.save()
            messages.success(request, f'Docente {docente.nombre_completo} asignado a {materia.nombre}.')
        else:
            # Remover docente
            materia.docente = None
            materia.save()
            messages.info(request, f'Docente removido de {materia.nombre}.')

        return redirect('detalle_carrera', carrera_id=materia.carrera.id)

    # GET: Mostrar formulario
    docentes = Funcionario.objects.filter(cargo='DOCENCIA', activo=True)

    context = {
        'materia': materia,
        'docentes': docentes,
        'carrera': materia.carrera,
    }

    return render(request, 'carreras/asignarDocente.html', context)


@login_required
def asignar_fechas(request, materia_id):
    materia = get_object_or_404(Materia, pk=materia_id)

    if request.method == 'POST':
        fecha_parcial = request.POST.get('fecha_examen_parcial')
        fecha_final = request.POST.get('fecha_examen_final')

        materia.fecha_examen_parcial = fecha_parcial if fecha_parcial else None
        materia.fecha_examen_final = fecha_final if fecha_final else None
        materia.save()

        messages.success(request, f'Fechas actualizadas para {materia.nombre}.')
        return redirect('detalle_carrera', carrera_id=materia.carrera.id)

    context = {
        'materia': materia,
        'carrera': materia.carrera,
    }

    return render(request, 'carreras/asignarFechas.html', context)

@login_required
@admin_required
def lista_usuarios(request):
    """Lista de usuarios del sistema (solo administradores)"""
    usuarios = User.objects.all().order_by('-date_joined')

    context = {
        'usuarios': usuarios,
        'usuarios_activos': User.objects.filter(is_active=True).count(),
        'total_admin': User.objects.filter(is_staff=True).count(),
        'total_estandar': User.objects.filter(is_staff=False).count(),
    }

    return render(request, 'usuarios/listaUsuarios.html', context)

@login_required
@admin_required
def crear_usuario(request):
    """Crear un nuevo usuario (solo administradores)"""
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                usuario.set_password(password)
            usuario.save()
            messages.success(request, f'Usuario {usuario.username} creado exitosamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm()

    return render(request, 'usuarios/formUsuarios.html', {
        'form': form,
        'titulo': 'Crear Nuevo Usuario',
        'boton': 'Crear Usuario'
    })

@login_required
@admin_required
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, 'usuarios/formUsuarios.html', {
        'form': form,
        'usuario': usuario,
        'titulo': f'Editar Usuario: {usuario.username}',
        'boton': 'Guardar Cambios'
    })

@login_required
@admin_required
def cambiar_estado_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)

    # No permitir desactivar superusuarios
    if usuario.is_superuser:
        messages.error(request, 'No puedes desactivar un superusuario.')
        return redirect('lista_usuarios')

    # Cambiar estado
    usuario.is_active = not usuario.is_active
    usuario.save()

    estado = "activado" if usuario.is_active else "desactivado"
    messages.success(request, f'Usuario {usuario.username} {estado} exitosamente.')

    return redirect('lista_usuarios')


@login_required
def mi_perfil(request):
    """Vista para que el usuario vea y edite su propio perfil"""
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('mi_perfil')
    else:
        form = PerfilForm(instance=request.user)

    return render(request, 'usuarios/miPerfil.html', {
        'form': form,
        'titulo': 'Mi Perfil'
    })


@login_required
def configuracion(request):
    """Vista de configuración (principalmente cambio de contraseña)"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantener la sesión iniciada
            messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('configuracion')
        else:
            messages.error(request, 'Por favor corrige los errores a continuación.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'usuarios/configuracion.html', {
        'form': form,
        'titulo': 'Configuración'
    })


@login_required
def lista_caja(request):
    """Vista principal del módulo de Caja con ingresos y egresos"""
    # Filtros
    sede_id = request.GET.get('sede')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    recibo = request.GET.get('recibo')
    cliente = request.GET.get('cliente')

    # Base querysets
    ingresos = Pago.objects.all().select_related('alumno', 'sede', 'carrera').order_by('-fecha', '-id')
    egresos = Egreso.objects.all().select_related('sede').order_by('-fecha', '-id')

    # Aplicar filtros
    if sede_id:
        ingresos = ingresos.filter(sede_id=sede_id)
        egresos = egresos.filter(sede_id=sede_id)

    if fecha_desde:
        ingresos = ingresos.filter(fecha__gte=fecha_desde)
        egresos = egresos.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        ingresos = ingresos.filter(fecha__lte=fecha_hasta)
        egresos = egresos.filter(fecha__lte=fecha_hasta)

    if recibo:
        ingresos = ingresos.filter(numero_recibo__icontains=recibo)
        egresos = egresos.filter(numero_comprobante__icontains=recibo)

    if cliente:
        ingresos = ingresos.filter(
            Q(alumno__nombre__icontains=cliente) |
            Q(alumno__apellido__icontains=cliente) |
            Q(nombre_cliente__icontains=cliente)
        )
        egresos = egresos.filter(concepto__icontains=cliente)

    # Calcular totales
    total_ingresos = ingresos.aggregate(Sum('importe_total'))['importe_total__sum'] or 0
    total_egresos = egresos.aggregate(Sum('monto'))['monto__sum'] or 0
    balance = total_ingresos - total_egresos

    # Limitar resultados
    ingresos = ingresos[:50]
    egresos = egresos[:50]

    sedes = Sede.objects.all().order_by('nombre')

    context = {
        'ingresos': ingresos,
        'egresos': egresos,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': balance,
        'sedes': sedes,
        'filtros': {
            'sede': sede_id,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'recibo': recibo,
            'cliente': cliente,
        }
    }

    return render(request, 'caja/listaCaja.html', context)


@login_required
@admin_required
def lista_egresos(request):
    """Vista para listar todos los egresos"""
    egresos = Egreso.objects.all().select_related('sede', 'usuario_registro').order_by('-fecha', '-id')

    # Filtros
    sede_id = request.GET.get('sede')
    categoria = request.GET.get('categoria')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if sede_id:
        egresos = egresos.filter(sede_id=sede_id)

    if categoria:
        egresos = egresos.filter(categoria=categoria)

    if fecha_desde:
        egresos = egresos.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        egresos = egresos.filter(fecha__lte=fecha_hasta)

    # Calcular total
    total_egresos = egresos.aggregate(Sum('monto'))['monto__sum'] or 0

    # Limitar a 100 registros
    egresos = egresos[:100]

    sedes = Sede.objects.all().order_by('nombre')

    context = {
        'egresos': egresos,
        'total_egresos': total_egresos,
        'sedes': sedes,
        'categorias': Egreso.CATEGORIA_CHOICES,
        'filtros': {
            'sede': sede_id,
            'categoria': categoria,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    }

    return render(request, 'caja/listaEgresos.html', context)


@login_required
def registrar_egreso(request):
    """Vista para registrar un nuevo egreso"""
    if request.method == 'POST':
        form = EgresoForm(request.POST, request.FILES)
        if form.is_valid():
            egreso = form.save(commit=False)
            egreso.usuario_registro = request.user
            egreso.save()
            messages.success(request, f'Egreso registrado exitosamente. Comprobante N° {egreso.numero_comprobante}')
            return redirect('detalle_egreso', egreso_uuid=egreso.uuid)
    else:
        form = EgresoForm()

    context = {
        'form': form,
        'titulo': 'Registrar Egreso',
        'boton': 'Registrar',
    }

    return render(request, 'caja/formEgreso.html', context)


@login_required
def detalle_egreso(request, egreso_uuid):
    """Vista para ver el detalle de un egreso"""
    egreso = get_object_or_404(Egreso.objects.select_related('sede', 'usuario_registro'), uuid=egreso_uuid)

    context = {
        'egreso': egreso,
    }

    return render(request, 'caja/detalleEgreso.html', context)


@login_required
def editar_egreso(request, egreso_uuid):
    """Vista para editar un egreso existente"""
    egreso = get_object_or_404(Egreso, uuid=egreso_uuid)

    if request.method == 'POST':
        form = EgresoForm(request.POST, request.FILES, instance=egreso)
        if form.is_valid():
            form.save()
            messages.success(request, f'Egreso actualizado exitosamente. Comprobante N° {egreso.numero_comprobante}')
            return redirect('detalle_egreso', egreso_uuid=egreso.uuid)
    else:
        form = EgresoForm(instance=egreso)

    context = {
        'form': form,
        'egreso': egreso,
        'titulo': 'Editar Egreso',
        'boton': 'Actualizar',
    }

    return render(request, 'caja/formEgreso.html', context)


@login_required
def eliminar_egreso(request, egreso_uuid):
    """Vista para eliminar un egreso o solicitar su eliminación"""
    egreso = get_object_or_404(Egreso, uuid=egreso_uuid)

    if request.method == 'POST':
        if request.user.is_staff:
            numero_comprobante = egreso.numero_comprobante
            egreso.delete()
            messages.success(request, f'Egreso con comprobante N° {numero_comprobante} eliminado exitosamente.')
            return redirect('lista_egresos')
        else:
            motivo = request.POST.get('motivo', 'No especificado')
            datos = {
                'numero_comprobante': egreso.numero_comprobante,
                'concepto': egreso.concepto,
                'monto': str(egreso.monto),
                'fecha': str(egreso.fecha)
            }
            SolicitudEliminacion.objects.create(
                usuario_solicita=request.user,
                modelo='EGRESO',
                objeto_id=egreso.id,
                motivo=motivo,
                datos_objeto=datos
            )
            messages.info(request, 'Solicitud de eliminación enviada al administrador.')
            return redirect('detalle_egreso', egreso_uuid=egreso.uuid)

    return redirect('lista_egresos')

@login_required
@admin_required
def informe_caja(request):
    """Informe completo de caja con balance de ingresos y egresos"""
    # Obtener parámetros
    sede_id = request.GET.get('sede')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    # Si no hay fechas, usar el mes actual
    if not fecha_desde or not fecha_hasta:
        hoy = timezone.now().date()
        fecha_desde = hoy.replace(day=1)
        # Último día del mes
        if hoy.month == 12:
            fecha_hasta = hoy.replace(day=31)
        else:
            fecha_hasta = (hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1))
    else:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()

    # Filtrar datos
    ingresos = Pago.objects.filter(fecha__gte=fecha_desde, fecha__lte=fecha_hasta)
    egresos = Egreso.objects.filter(fecha__gte=fecha_desde, fecha__lte=fecha_hasta)

    if sede_id:
        ingresos = ingresos.filter(sede_id=sede_id)
        egresos = egresos.filter(sede_id=sede_id)
        sede = get_object_or_404(Sede, id=sede_id)
    else:
        sede = None

    # Ordenar por fecha
    ingresos = ingresos.select_related('alumno', 'sede', 'carrera').order_by('fecha')
    egresos = egresos.select_related('sede').order_by('fecha')

    # Calcular totales
    total_ingresos = ingresos.aggregate(Sum('importe_total'))['importe_total__sum'] or 0
    total_egresos = egresos.aggregate(Sum('monto'))['monto__sum'] or 0
    balance = total_ingresos - total_egresos

    # Agrupar egresos por categoría
    egresos_por_categoria = {}
    for egreso in egresos:
        categoria = egreso.get_categoria_display()
        if categoria not in egresos_por_categoria:
            egresos_por_categoria[categoria] = 0
        egresos_por_categoria[categoria] += egreso.monto

    context = {
        'sede': sede,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'ingresos': ingresos,
        'egresos': egresos,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': balance,
        'egresos_por_categoria': egresos_por_categoria,
        'sedes': Sede.objects.all().order_by('nombre'),
    }

    return render(request, 'caja/informeCaja.html', context)

@login_required
@admin_required
def lista_solicitudes_eliminacion(request):
    """Lista de solicitudes de eliminación para administradores"""
    solicitudes = SolicitudEliminacion.objects.all().select_related('usuario_solicita').order_by('-fecha_solicitud')
    
    context = {
        'solicitudes': solicitudes,
        'pendientes': solicitudes.filter(estado='PENDIENTE').count()
    }
    return render(request, 'usuarios/listaSolicitudesEliminacion.html', context)

@login_required
@admin_required
def procesar_solicitud_eliminacion(request, solicitud_id):
    """Aprobar o rechazar una solicitud de eliminación"""
    solicitud = get_object_or_404(SolicitudEliminacion, id=solicitud_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion') # 'APROBAR' o 'RECHAZAR'
        observaciones = request.POST.get('observaciones', '')
        
        solicitud.usuario_decide = request.user
        solicitud.fecha_decision = timezone.now()
        solicitud.observaciones_decision = observaciones
        
        if accion == 'APROBAR':
            solicitud.estado = 'APROBADO'
            # Eliminar el objeto real
            try:
                if solicitud.modelo == 'PAGO':
                    obj = Pago.objects.get(id=solicitud.objeto_id)
                elif solicitud.modelo == 'EGRESO':
                    obj = Egreso.objects.get(id=solicitud.objeto_id)
                elif solicitud.modelo == 'ALUMNO':
                    obj = Alumno.objects.get(id=solicitud.objeto_id)
                elif solicitud.modelo == 'CARRERA':
                    obj = Carrera.objects.get(id=solicitud.objeto_id)
                elif solicitud.modelo == 'MATERIA':
                    obj = Materia.objects.get(id=solicitud.objeto_id)
                elif solicitud.modelo == 'FUNCIONARIO':
                    obj = Funcionario.objects.get(id=solicitud.objeto_id)
                elif solicitud.modelo == 'SEDE':
                    obj = Sede.objects.get(id=solicitud.objeto_id)
                
                obj.delete()
                messages.success(request, f'Solicitud aprobada y objeto eliminado.')
            except Exception as e:
                messages.error(request, f'Error al eliminar el objeto: {str(e)}')
                solicitud.estado = 'PENDIENTE' # Revertir si falló la eliminación real
        else:
            solicitud.estado = 'RECHAZADO'
            messages.info(request, 'Solicitud de eliminación rechazada.')
        
        solicitud.save()
        return redirect('lista_solicitudes_eliminacion')
    
    return redirect('lista_solicitudes_eliminacion')
