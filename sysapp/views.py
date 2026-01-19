
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, datetime
from django.db.models import Max


from . import models
from .models import Sede, Alumno, Funcionario, Pago, Carrera, AsistenciaFuncionario, Materia
from .forms import PagoForm, AlumnoForm, FuncionarioForm, AsistenciaForm, SedeForm, CarreraForm, UsuarioForm, \
    MateriaForm
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
    pagos_recientes = Pago.objects.select_related('alumno', 'sede').order_by('-fecha_creacion')[:10]

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
def detalle_alumno(request, alumno_id):
    """Detalle de un alumno con historial de pagos"""
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    pagos = alumno.pagos.all().order_by('-fecha')

    context = {
        'alumno': alumno,
        'pagos': pagos,
        'total_pagado': pagos.aggregate(Sum('importe_total'))['importe_total__sum'] or 0,
        'puede_rendir': alumno.puede_rendir_examen,
        'total_estrellas': alumno.total_estrellas,
    }

    return render(request, 'alumnos/detalleAlumnos.html', context)


@login_required
def crear_alumno(request):
    """Crear un nuevo alumno"""
    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            alumno = form.save()
            messages.success(request, f'Alumno {alumno.nombre} {alumno.apellido} registrado exitosamente.')
            return redirect('detalle_alumno', alumno_id=alumno.id)
    else:
        form = AlumnoForm()

    return render(request, 'alumnos/formAlumnos.html', {
        'form': form,
        'titulo': 'Registrar Nuevo Alumno',
        'boton': 'Registrar Alumno'
    })


@login_required
def editar_alumno(request, alumno_id):
    """Editar un alumno existente"""
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    if request.method == 'POST':
        form = AlumnoForm(request.POST, instance=alumno)
        if form.is_valid():
            form.save()
            messages.success(request, f'Alumno {alumno.nombre} {alumno.apellido} actualizado exitosamente.')
            return redirect('detalle_alumno', alumno_id=alumno.id)
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
    """Vista para buscar alumnos (útil para autocompletado)"""
    from django.http import JsonResponse

    query = request.GET.get('q', '')
    if len(query) >= 2:
        alumnos = Alumno.objects.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(documento__icontains=query)
        )[:10]

        resultados = [{
            'id': alumno.id,
            'nombre_completo': alumno.nombre_completo,
            'documento': alumno.documento,
            'sede': alumno.sede.nombre if alumno.sede else ''
        } for alumno in alumnos]

        return JsonResponse({'resultados': resultados})

    return JsonResponse({'resultados': []})

#Pagos

@login_required
def lista_pagos(request):
    """Vista para listar todos los pagos con filtros"""
    pagos = Pago.objects.all().select_related('alumno', 'sede').order_by('-fecha', '-id')

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
def detalle_pago(request, id):
    """Vista para ver el detalle completo de un pago"""
    pago = get_object_or_404(Pago.objects.select_related('alumno', 'sede'), id=id)

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

            # Generar número de recibo automáticamente si es necesario
            if not pago.numero_recibo:
                ultimo_pago = Pago.objects.all().order_by('-id').first()
                if ultimo_pago and ultimo_pago.numero_recibo:
                    try:
                        ultimo_numero = int(ultimo_pago.numero_recibo)
                        pago.numero_recibo = str(ultimo_numero + 1).zfill(6)
                    except ValueError:
                        pago.numero_recibo = '000001'
                else:
                    pago.numero_recibo = '000001'

            # Guardar campos adicionales de cliente diferenciado
            if form.cleaned_data.get('es_cliente_diferenciado'):
                pago.nombre_cliente = form.cleaned_data.get('nombre_cliente')
                pago.validez_pago = form.cleaned_data.get('validez_pago')
                pago.fecha_vencimiento = form.cleaned_data.get('fecha_vencimiento')
                pago.curso = form.cleaned_data.get('curso')
                pago.monto_unitario = form.cleaned_data.get('monto_unitario')
                pago.cantidad_cuotas = form.cleaned_data.get('cantidad_cuotas', 1)
                pago.alumno = None  # No tiene alumno asociado

            pago.save()
            messages.success(request, f'Pago registrado exitosamente. Recibo N° {pago.numero_recibo}')
            return redirect('detalle_pago', id=pago.id)
    else:
        form = PagoForm()

    context = {
        'form': form,
        'titulo': 'Registrar Pago',
        'boton': 'Registrar',
    }

    return render(request, 'pagos/formPagos.html', context)


@login_required
def editar_pago(request, id):
    """Vista para editar un pago existente"""
    pago = get_object_or_404(Pago, id=id)

    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES, instance=pago)
        if form.is_valid():
            pago = form.save(commit=False)

            # Actualizar campos de cliente diferenciado
            if form.cleaned_data.get('es_cliente_diferenciado'):
                pago.nombre_cliente = form.cleaned_data.get('nombre_cliente')
                pago.validez_pago = form.cleaned_data.get('validez_pago')
                pago.fecha_vencimiento = form.cleaned_data.get('fecha_vencimiento')
                pago.curso = form.cleaned_data.get('curso')
                pago.monto_unitario = form.cleaned_data.get('monto_unitario')
                pago.cantidad_cuotas = form.cleaned_data.get('cantidad_cuotas', 1)
                pago.alumno = None
            else:
                # Si cambió de cliente diferenciado a alumno regular, limpiar campos
                pago.nombre_cliente = None
                pago.validez_pago = None
                pago.curso = None
                pago.monto_unitario = None
                pago.cantidad_cuotas = None

            pago.save()
            messages.success(request, f'Pago actualizado exitosamente. Recibo N° {pago.numero_recibo}')
            return redirect('detalle_pago', id=pago.id)
    else:
        form = PagoForm(instance=pago)

    context = {
        'form': form,
        'pago': pago,
        'titulo': 'Editar Pago',
        'boton': 'Actualizar',
    }

    return render(request, 'pagos/formPagos.html', context)


@login_required
def eliminar_pago(request, id):
    """Vista para eliminar un pago"""
    pago = get_object_or_404(Pago, id=id)

    if request.method == 'POST':
        numero_recibo = pago.numero_recibo
        pago.delete()
        messages.success(request, f'Pago con recibo N° {numero_recibo} eliminado exitosamente.')
        return redirect('lista_pagos')

    # Si no es POST, redirigir a la lista
    return redirect('lista_pagos')

# VISTAS DE FUNCIONARIOS

@login_required
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
def lista_sedes(request):
    """Lista de todas las sedes con rendición del día"""
    sedes = Sede.objects.filter(activa=True)
    hoy = timezone.now().date()

    sedes_data = []
    for sede in sedes:
        rendicion = sede.rendicion_dia(hoy)
        sedes_data.append({
            'sede': sede,
            'alumnos_activos': sede.alumnos.filter(activo=True).count(),
            'funcionarios_activos': sede.funcionarios.filter(activo=True).count(),
            'ingresos_hoy': rendicion['total'],
            'pagos_hoy': rendicion['cantidad_pagos'],
        })

    context = {
        'sedes_data': sedes_data,
        'fecha': hoy,
    }

    return render(request, 'sedes/listaSedes.html', context)


@login_required
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
@admin_required
def detalle_carrera(request, carrera_id):
    carrera = get_object_or_404(Carrera, pk=carrera_id)
    materias = carrera.materias.all().select_related('docente')

    context = {
        'carrera': carrera,
        'materias': materias,
    }

    return render(request, 'carreras/detalleCarrera.html', context)


@login_required
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
    """Editar un usuario existente (solo administradores)"""
    usuario = get_object_or_404(User, pk=usuario_id)

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, 'usuarios/formCarreras.html', {
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
def buscar_alumno(request):
    """Vista para buscar alumnos (útil para autocompletado)"""
    from django.http import JsonResponse

    query = request.GET.get('q', '')
    if len(query) >= 2:
        alumnos = Alumno.objects.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(documento__icontains=query)
        )[:10]

        resultados = [{
            'id': alumno.id,
            'nombre_completo': alumno.nombre_completo,
            'documento': alumno.documento,
            'sede': alumno.sede.nombre if alumno.sede else ''
        } for alumno in alumnos]

        return JsonResponse({'resultados': resultados})

    return JsonResponse({'resultados': []})