from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.db.models import Sum, Count, Q
from django.template import context
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import timedelta, datetime, date
import json
from django.db.models import Max
from dateutil.relativedelta import relativedelta

from .models import (
    Sede, Alumno, Funcionario, Pago, Carrera,
    AsistenciaFuncionario, Materia, Egreso,
    CanjeEstrellas, SolicitudEliminacion, CuentaBancaria,
)
from .forms import (
    PagoForm, AlumnoForm, FuncionarioForm, AsistenciaForm,
    SedeForm, CarreraForm, UsuarioForm, MateriaForm, EgresoForm, PerfilForm,
)
from .decorators import admin_required


#  AUTENTICACIÓN

def login_view(request):
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
                return redirect(request.GET.get('next', 'dashboard'))
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
        user = User.objects.create_user(
            username=request.POST['username'],
            email=request.POST['email'],
            password=request.POST['password'],
        )
        login(request, user)
        return redirect('login')
    return render(request, 'registrar.html')

#  DASHBOARD

@login_required
def dashboard(request):
    hoy = timezone.now().date()
    total_alumnos      = Alumno.objects.filter(activo=True).count()
    total_funcionarios = Funcionario.objects.filter(activo=True).count()
    total_carreras     = Carrera.objects.filter(activa=True).count()
    total_sedes        = Sede.objects.filter(activa=True).count()

    pagos_hoy     = Pago.objects.filter(fecha=hoy)
    ingresos_hoy  = pagos_hoy.aggregate(Sum('importe_total'))['importe_total__sum'] or 0

    alumnos_activos      = Alumno.objects.filter(activo=True)
    alumnos_al_dia       = sum(1 for a in alumnos_activos if a.estado_pagos == 'AL_DIA')
    alumnos_por_vencer   = sum(1 for a in alumnos_activos if a.estado_pagos == 'CERCANO_VENCIMIENTO')
    alumnos_atrasados    = sum(1 for a in alumnos_activos if a.estado_pagos == 'ATRASADO')

    pagos_recientes = Pago.objects.select_related('alumno', 'sede', 'carrera').order_by('-fecha_creacion')[:10]

    return render(request, 'inicio.html', {
        'total_alumnos':       total_alumnos,
        'total_funcionarios':  total_funcionarios,
        'total_carreras':      total_carreras,
        'total_sedes':         total_sedes,
        'ingresos_hoy':        ingresos_hoy,
        'cantidad_pagos_hoy':  pagos_hoy.count(),
        'alumnos_al_dia':      alumnos_al_dia,
        'alumnos_por_vencer':  alumnos_por_vencer,
        'alumnos_atrasados':   alumnos_atrasados,
        'pagos_recientes':     pagos_recientes,
    })

#  ALUMNOS

@login_required
def lista_alumnos(request):
    # Obtener la sede del perfil del usuario si no es admin
    user_sede = None
    if not request.user.is_staff:  # Si NO es administrador
        try:
            user_sede = request.user.perfil.sede
            if not user_sede:
                messages.warning(request, 'Tu usuario no tiene una sede asignada. Contacta al administrador.')
                return render(request, 'alumnos/listaAlumnos.html', {
                    'alumnos': [],
                    'total_al_dia': 0,
                    'total_por_vencer': 0,
                    'total_atrasados': 0,
                    'total_alumnos': 0,
                    'sedes': Sede.objects.none(),
                    'carreras': Carrera.objects.filter(activa=True),
                    'filtros': {},
                    'user_sede': None,
                    'is_staff': False,
                })
        except (AttributeError, PerfilUsuario.DoesNotExist):
            messages.warning(request,
                             'Tu perfil de usuario no está configurado correctamente. Contacta al administrador.')
            return render(request, 'alumnos/listaAlumnos.html', {
                'alumnos': [],
                'total_al_dia': 0,
                'total_por_vencer': 0,
                'total_atrasados': 0,
                'total_alumnos': 0,
                'sedes': Sede.objects.none(),
                'carreras': Carrera.objects.filter(activa=True),
                'filtros': {},
                'user_sede': None,
                'is_staff': False,
            })

    # Obtener parámetros de filtro
    sede_id = request.GET.get('sede')
    carrera_id = request.GET.get('carrera')
    estado = request.GET.get('estado')
    busqueda = request.GET.get('busqueda')

    # Base queryset - filtrar por sede del usuario si no es admin
    alumnos_qs = Alumno.objects.filter(activo=True).select_related('carrera', 'sede')

    # APLICAR FILTRO DE SEDE SEGÚN PERFIL
    if not request.user.is_staff and user_sede:
        # Si no es admin, solo ver alumnos de SU sede
        alumnos_qs = alumnos_qs.filter(sede=user_sede)
    elif sede_id and request.user.is_staff:
        # Si es admin y seleccionó una sede específica
        alumnos_qs = alumnos_qs.filter(sede_id=sede_id)

    # Convertir a lista para filtrar por estado_pagos (que es property)
    todos_activos = list(alumnos_qs)

    # Calcular totales por estado (para las cards)
    total_al_dia = sum(1 for a in todos_activos if a.estado_pagos == 'AL_DIA')
    total_por_vencer = sum(1 for a in todos_activos if a.estado_pagos == 'CERCANO_VENCIMIENTO')
    total_atrasados = sum(1 for a in todos_activos if a.estado_pagos == 'ATRASADO')
    total_alumnos = len(todos_activos)

    # Aplicar filtros adicionales (en Python porque estado_pagos es property)
    alumnos = todos_activos

    if carrera_id:
        alumnos = [a for a in alumnos if str(a.carrera_id) == carrera_id]
    if busqueda:
        b = busqueda.lower()
        alumnos = [
            a for a in alumnos
            if b in a.nombre.lower()
               or b in a.apellido.lower()
               or b in (a.cedula or '').lower()
               or (a.carrera and b in a.carrera.nombre.lower())
               or (a.sede and b in a.sede.nombre.lower())
        ]
    if estado:
        alumnos = [a for a in alumnos if a.estado_pagos == estado]

    # Determinar qué sedes mostrar en los filtros
    if request.user.is_staff:
        # Admin ve todas las sedes
        sedes = Sede.objects.filter(activa=True)
    else:
        # Usuario normal ve SOLO su sede
        sedes = Sede.objects.filter(id=user_sede.id) if user_sede else Sede.objects.none()

    return render(request, 'alumnos/listaAlumnos.html', {
        'alumnos': alumnos,
        'total_al_dia': total_al_dia,
        'total_por_vencer': total_por_vencer,
        'total_atrasados': total_atrasados,
        'total_alumnos': total_alumnos,
        'sedes': sedes,
        'carreras': Carrera.objects.filter(activa=True),
        'filtros': {
            'sede': sede_id,
            'carrera': carrera_id,
            'estado': estado,
            'busqueda': busqueda,
        },
        'user_sede': user_sede,
        'is_staff': request.user.is_staff,
    })

@login_required
def detalle_alumno(request, alumno_uuid):
    alumno = get_object_or_404(Alumno, uuid=alumno_uuid)
    hoy = date.today()

    # ── Pagos del alumno (excluir matrículas, ordenar del más reciente) ──────
    pagos = alumno.pagos.all().order_by('-fecha')

    # ── Canjes ────────────────────────────────────────────────────────────────
    canjes = alumno.canjes.all().order_by('-fecha')

    # ── Total pagado ──────────────────────────────────────────────────────────
    total_pagado = alumno.pagos.filter(
        es_matricula=False
    ).aggregate(total=Sum('importe_total'))['total'] or 0

    # ── Total de estrellas (puntos) actuales ──────────────────────────────────
    puntos_ganados = alumno.pagos.filter(
        es_matricula=False
    ).aggregate(total=Sum('puntos'))['total'] or 0

    puntos_canjeados = alumno.canjes.aggregate(
        total=Sum('cantidad')
    )['total'] or 0

    total_estrellas = max(0, puntos_ganados - puntos_canjeados)

    ultimo_pago_con_vigencia = alumno.pagos.filter(
        es_matricula=False,
        valido_hasta__isnull=False,
    ).order_by('-valido_hasta').first()

    valido_hasta = None
    estado_cobertura = 'SIN_PAGOS'

    if ultimo_pago_con_vigencia:
        valido_hasta = ultimo_pago_con_vigencia.valido_hasta

        dias_restantes = (valido_hasta - hoy).days

        if dias_restantes < 0:
            estado_cobertura = 'VENCIDO'
        elif dias_restantes <= 10:
            estado_cobertura = 'POR_VENCER'
        else:
            estado_cobertura = 'AL_DIA'

    return render(request, 'alumnos/detalleAlumnos.html', {
        'alumno':           alumno,
        'pagos':            pagos,
        'canjes':           canjes,
        'total_pagado':     total_pagado,
        'total_estrellas':  total_estrellas,
        'estado_cobertura': estado_cobertura,
        'valido_hasta':     valido_hasta,
    })


@login_required
def canjear_estrellas(request, alumno_uuid):
    if request.method == 'POST':
        alumno   = get_object_or_404(Alumno, uuid=alumno_uuid)
        cantidad = int(request.POST.get('cantidad', 0))
        concepto = request.POST.get('concepto', '').strip()

        if cantidad <= 0:
            messages.error(request, 'La cantidad de puntos debe ser mayor a cero.')
        elif cantidad > alumno.total_puntos:   # ← renombrado
            messages.error(request, 'El alumno no tiene suficientes puntos para este canje.')
        elif not concepto:
            messages.error(request, 'Debe especificar el concepto del canje.')
        else:
            CanjeEstrellas.objects.create(
                alumno=alumno,
                cantidad=cantidad,
                concepto=concepto,
                usuario_registro=request.user,
            )
            messages.success(request, f'Se han canjeado {cantidad} puntos exitosamente.')
    return redirect('detalle_alumno', alumno_uuid=alumno_uuid)


@login_required
def crear_alumno(request):
    """Crear un nuevo alumno.

    Si el POST incluye add_another=1 (botón "Guardar y añadir otro"),
    tras guardar redirige al formulario vacío en lugar de al detalle.
    """
    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            alumno = form.save()
            add_another = request.POST.get('add_another', '0') == '1'
            messages.success(
                request,
                f'Alumno {alumno.nombre} {alumno.apellido} registrado exitosamente.'
            )
            if add_another:
                # Redirigir al mismo formulario vacío para el próximo alumno
                return redirect('crear_alumno')
            return redirect('detalle_alumno', alumno_uuid=alumno.uuid)
    else:
        form = AlumnoForm()

    return render(request, 'alumnos/formAlumnos.html', {
        'form':   form,
        'titulo': 'Registrar Nuevo Alumno',
        'boton':  'Guardar Alumno',
        # 'alumno' NO se pasa en creación → el template muestra el botón "Añadir otro"
    })


@login_required
def editar_alumno(request, alumno_uuid):
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
        'form': form, 'alumno': alumno,
        'titulo': f'Editar Alumno: {alumno.nombre_completo}', 'boton': 'Guardar Cambios',
    })


@login_required
def buscar_alumno(request):
    """Autocompletado AJAX — incluye monto_matricula para el formulario."""
    query = request.GET.get('q', '').strip()
    if len(query) >= 2:
        alumnos = Alumno.objects.select_related('sede', 'carrera').filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(cedula__icontains=query)
        )[:10]

        resultados = [{
            'id':               alumno.id,
            'nombre_completo':  alumno.nombre_completo,
            'cedula':           alumno.cedula,
            'sede_id':          alumno.sede_id,
            'sede':             alumno.sede.nombre if alumno.sede else '',
            'carrera_id':       alumno.carrera_id,
            'carrera':          alumno.carrera.nombre if alumno.carrera else '',
            'monto_mensualidad':str(alumno.carrera.monto_mensualidad) if alumno.carrera else '',
            'monto_matricula':  str(alumno.carrera.monto_matricula)   if alumno.carrera else '',
        } for alumno in alumnos]

        return JsonResponse({'resultados': resultados})
    return JsonResponse({'resultados': []})

#  CUENTAS BANCARIAS  (endpoint AJAX)

@login_required
@require_http_methods(["GET", "POST"])
def cuentas_bancarias(request):
    """
    GET  → devuelve lista de cuentas activas (para tarjetas del formulario).
    POST → crea o recupera una cuenta bancaria y la devuelve.
    """
    if request.method == "GET":
        cuentas = CuentaBancaria.objects.filter(activa=True).values('id', 'entidad', 'titular')
        return JsonResponse({'cuentas': list(cuentas)})

    # POST
    try:
        data    = json.loads(request.body)
        entidad = data.get('entidad', '').strip()
        titular = data.get('titular', '').strip()

        if not entidad or not titular:
            return JsonResponse({'error': 'Entidad y titular son requeridos.'}, status=400)

        cuenta, created = CuentaBancaria.objects.get_or_create(
            entidad__iexact=entidad,
            titular__iexact=titular,
            defaults={'entidad': entidad, 'titular': titular},
        )
        return JsonResponse({
            'id':      cuenta.id,
            'entidad': cuenta.entidad,
            'titular': cuenta.titular,
            'created': created,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

#  PAGOS

def _carreras_data_json():
    """JSON con id, monto_mensualidad y monto_matricula para el template."""
    return json.dumps(
        list(Carrera.objects.values('id', 'monto_mensualidad', 'monto_matricula')),
        default=str,
    )


def _cuentas_data_json():
    """JSON con las cuentas bancarias activas."""
    return json.dumps(
        list(CuentaBancaria.objects.filter(activa=True).values('id', 'entidad', 'titular')),
        default=str,
    )


def _guardar_cuenta_bancaria_si_nueva(request, pago):
    """
    Si el usuario seleccionó 'OTRO' banco y proporcionó entidad/titular,
    crea la cuenta (o recupera la existente) y la asocia al pago.
    Si seleccionó una cuenta existente, la asocia directamente.
    """
    if pago.metodo_pago != 'TRANSFERENCIA':
        pago.cuenta_bancaria = None
        return

    cuenta_id = request.POST.get('cuenta_bancaria_id', '').strip()
    otro_entidad = request.POST.get('otro_banco_entidad', '').strip()
    otro_titular = request.POST.get('otro_banco_titular', '').strip()

    if cuenta_id and cuenta_id.isdigit():
        try:
            pago.cuenta_bancaria = CuentaBancaria.objects.get(id=int(cuenta_id))
        except CuentaBancaria.DoesNotExist:
            pago.cuenta_bancaria = None
    elif otro_entidad and otro_titular:
        cuenta, _ = CuentaBancaria.objects.get_or_create(
            entidad__iexact=otro_entidad,
            titular__iexact=otro_titular,
            defaults={'entidad': otro_entidad, 'titular': otro_titular},
        )
        pago.cuenta_bancaria = cuenta
    else:
        pago.cuenta_bancaria = None


@login_required
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

    # Calcular el total de pagos (antes de limitar a 100)
    total_pagos = pagos.aggregate(total=Sum('importe_total'))['total'] or 0

    # Limitar a 100 registros
    pagos = pagos[:100]

    # Obtener todas las sedes para el filtro
    sedes = Sede.objects.all().order_by('nombre')

    context = {
        'pagos': pagos,
        'sedes': sedes,
        'total_pagos': total_pagos,  # ← Esta línea es la que faltaba
    }

    return render(request, 'pagos/listaPagos.html', context)

@login_required
def detalle_pago(request, pago_uuid):
    pago = get_object_or_404(
        Pago.objects.select_related('alumno', 'sede', 'carrera', 'cuenta_bancaria'),
        uuid=pago_uuid,
    )
    return render(request, 'pagos/detallePago.html', {'pago': pago})


@login_required
def registrar_pago(request):
    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.usuario_registro = request.user

            es_cliente_diferenciado = form.cleaned_data.get('es_cliente_diferenciado')

            # Campos directos del form
            pago.es_matricula     = form.cleaned_data.get('es_matricula', False)
            pago.metodo_pago      = form.cleaned_data.get('metodo_pago', 'EFECTIVO')
            pago.numero_recibo    = pago.numero_recibo or None
            pago.nombre_cliente   = form.cleaned_data.get('nombre_cliente') if es_cliente_diferenciado else None
            pago.alumno           = None if es_cliente_diferenciado else form.cleaned_data.get('alumno')
            pago.carrera          = form.cleaned_data.get('carrera') or (pago.alumno.carrera if pago.alumno else None)
            pago.validez_pago     = form.cleaned_data.get('validez_pago')
            pago.monto_unitario   = form.cleaned_data.get('monto_unitario')
            pago.cantidad_cuotas  = form.cleaned_data.get('cantidad_cuotas') or 1

            # carrera_otro: guardar como texto si no hay FK de carrera
            carrera_otro = form.cleaned_data.get('carrera_otro', '').strip()

            if not pago.carrera and carrera_otro:
                # Si el modelo tiene el campo carrera_otro (CharField), lo guarda
                if hasattr(pago, 'carrera_otro'):
                    pago.carrera_otro = carrera_otro

            # Matrícula: limpiar campos de cuota
            if pago.es_matricula:
                pago.fecha_vencimiento = None
                pago.numero_cuota      = None
                pago.puntos = 0
            else:
                pago.fecha_vencimiento = form.cleaned_data.get('fecha_vencimiento')

            pago.save()

            # Asociar cuenta bancaria DESPUÉS del save (necesita pk)
            _guardar_cuenta_bancaria_si_nueva(request, pago)
            pago.save(update_fields=['cuenta_bancaria'])

            if pago.numero_recibo:
                messages.success(request, f'Pago registrado exitosamente. Recibo No. {pago.numero_recibo}')
            else:
                messages.success(request, 'Pago registrado exitosamente.')
            return redirect('detalle_pago', pago_uuid=pago.uuid)
    else:
        form = PagoForm()

    return render(request, 'pagos/formPagos.html', {
        'form':              form,
        'titulo':            'Registrar Pago',
        'boton':             'Registrar',
        'carreras_data':     _carreras_data_json(),
        'cuentas_bancarias': _cuentas_data_json(),
    })


@login_required
@admin_required
def editar_pago(request, pago_uuid):
    pago = get_object_or_404(Pago, uuid=pago_uuid)

    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES, instance=pago)
        if form.is_valid():
            pago = form.save(commit=False)
            es_cliente_diferenciado = form.cleaned_data.get('es_cliente_diferenciado')
            pago.es_matricula = form.cleaned_data.get('es_matricula', False)
            pago.metodo_pago = form.cleaned_data.get('metodo_pago', 'EFECTIVO')
            pago.numero_recibo = pago.numero_recibo or None
            pago.nombre_cliente = form.cleaned_data.get('nombre_cliente') if es_cliente_diferenciado else None
            pago.alumno = None if es_cliente_diferenciado else form.cleaned_data.get('alumno')
            pago.carrera = form.cleaned_data.get('carrera') or (pago.alumno.carrera if pago.alumno else None)
            pago.validez_pago     = form.cleaned_data.get('validez_pago')
            pago.monto_unitario   = form.cleaned_data.get('monto_unitario')
            pago.cantidad_cuotas  = form.cleaned_data.get('cantidad_cuotas') or 1

            carrera_otro = form.cleaned_data.get('carrera_otro', '').strip()
            if not pago.carrera and carrera_otro and hasattr(pago, 'carrera_otro'):
                pago.carrera_otro = carrera_otro

            if pago.es_matricula:
                pago.fecha_vencimiento = None
                pago.numero_cuota      = None
                pago.puntos            = 0
            else:
                pago.fecha_vencimiento = form.cleaned_data.get('fecha_vencimiento')

            pago.save()

            _guardar_cuenta_bancaria_si_nueva(request, pago)
            pago.save(update_fields=['cuenta_bancaria'])

            if pago.numero_recibo:
                messages.success(request, f'Pago actualizado exitosamente. Recibo No. {pago.numero_recibo}')
            else:
                messages.success(request, 'Pago actualizado exitosamente.')
            return redirect('detalle_pago', pago_uuid=pago.uuid)
    else:
        form = PagoForm(instance=pago)

    return render(request, 'pagos/formPagos.html', {
        'form':                   form,
        'pago':                   pago,
        'titulo':                 'Editar Pago',
        'boton':                  'Actualizar',
        'carreras_data':          _carreras_data_json(),
        'cuentas_bancarias':      _cuentas_data_json(),
        'cuenta_bancaria_actual': pago.cuenta_bancaria_id,
    })


@login_required
@admin_required
def eliminar_pago(request, pago_uuid):
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
            SolicitudEliminacion.objects.create(
                usuario_solicita=request.user,
                modelo='PAGO',
                objeto_id=pago.id,
                motivo=motivo,
                datos_objeto={
                    'numero_recibo': pago.numero_recibo,
                    'pagador': pago.nombre_pagador,
                    'monto':  str(pago.importe_total),
                    'fecha':  str(pago.fecha),
                },
            )
            messages.info(request, 'Solicitud de eliminación enviada al administrador.')
            return redirect('detalle_pago', pago_uuid=pago.uuid)
    return redirect('lista_pagos')

#  FUNCIONARIOS

def lista_funcionarios(request):
    funcionarios = Funcionario.objects.select_related('sede').all()

    # Filtros
    cargo = request.GET.get('cargo')
    sede  = request.GET.get('sede')
    activo = request.GET.get('activo')

    if cargo:
        funcionarios = funcionarios.filter(cargo=cargo)
    if sede:
        funcionarios = funcionarios.filter(sede_id=sede)
    if activo:
        funcionarios = funcionarios.filter(activo=(activo == 'true'))

    #Totales para las stat-cards
    todos = Funcionario.objects.all()

    context = {
        'funcionarios':        funcionarios,
        'total_funcionarios':  funcionarios.count(),
        'sedes':               Sede.objects.all(),
        'cargos':              Funcionario.CARGO_CHOICES,

        'total_docencia':      todos.filter(cargo='DOCENCIA').count(),
        'total_administrativo': todos.filter(cargo='ADMINISTRATIVO').count(),
        'total_direccion':     todos.filter(cargo='DIRECCION').count(),
        'total_activos':       todos.filter(activo=True).count(),
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
        'form': form, 'titulo': 'Registrar Nuevo Funcionario', 'boton': 'Registrar Funcionario',
    })


@login_required
def registrar_asistencia(request):
    if request.method == 'POST':
        form = AsistenciaForm(request.POST)
        if form.is_valid():
            asistencia = form.save()
            estado = "Presente" if asistencia.presente else "Ausente"
            messages.success(request, f'Asistencia registrada: {asistencia.funcionario.nombre_completo} - {estado}')
            return redirect('lista_asistencias')
    else:
        form = AsistenciaForm(initial={'fecha': timezone.now().date(), 'presente': True})
    return render(request, 'funcionarios/formAsistencia.html', {
        'form': form, 'titulo': 'Registrar Asistencia', 'boton': 'Registrar Asistencia',
    })


@login_required
def lista_asistencias(request):
    asistencias  = AsistenciaFuncionario.objects.all().select_related('funcionario').order_by('-fecha')
    fecha        = request.GET.get('fecha')
    funcionario_id = request.GET.get('funcionario')
    if fecha:          asistencias = asistencias.filter(fecha=fecha)
    if funcionario_id: asistencias = asistencias.filter(funcionario_id=funcionario_id)
    return render(request, 'funcionarios/listaAsistencias.html', {
        'asistencias':  asistencias[:50],
        'funcionarios': Funcionario.objects.filter(activo=True),
    })

@login_required
def detalle_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, pk=funcionario_id)

    hoy   = timezone.now().date()
    anio  = int(request.GET.get('anio', hoy.year))
    mes   = int(request.GET.get('mes',  hoy.month))

    asistencias_mes = funcionario.asistencias.filter(
        fecha__year=anio, fecha__month=mes
    ).order_by('-fecha')

    # ── Totales del mes seleccionado ──────────────────────────────────
    total_presencias = asistencias_mes.filter(presente=True).count()
    total_ausencias  = asistencias_mes.filter(presente=False).count()
    total_horas_mes  = asistencias_mes.aggregate(
        models.Sum('horas_trabajadas')
    )['horas_trabajadas__sum'] or 0

    egresos = funcionario.egresos_funcionario.all().order_by('-fecha')
    total_egresos_pagados = funcionario.total_egresos()

    historial_asistencias = funcionario.asistencias.all()[:50]

    MESES = [
        (1,'Enero'),(2,'Febrero'),(3,'Marzo'),(4,'Abril'),
        (5,'Mayo'),(6,'Junio'),(7,'Julio'),(8,'Agosto'),
        (9,'Septiembre'),(10,'Octubre'),(11,'Noviembre'),(12,'Diciembre'),
    ]
    anios_disponibles = list(range(hoy.year - 3, hoy.year + 1))

    return render(request, 'funcionarios/detalleFuncionario.html', {
        'funcionario':          funcionario,
        'asistencias_mes':      asistencias_mes,
        'total_presencias':     total_presencias,
        'total_ausencias':      total_ausencias,
        'total_horas_mes':      total_horas_mes,
        'egresos':              egresos,
        'total_egresos_pagados':total_egresos_pagados,
        'historial_asistencias':historial_asistencias,
        'mes_seleccionado':     mes,
        'anio_seleccionado':    anio,
        'meses':                MESES,
        'anios':                anios_disponibles,
    })

@login_required
def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, pk=funcionario_id)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Funcionario {funcionario.nombre_completo} actualizado exitosamente.')
            return redirect('detalle_funcionario', funcionario_id=funcionario.id)
    else:
        form = FuncionarioForm(instance=funcionario)
    return render(request, 'funcionarios/formFuncionario.html', {
        'form':       form,
        'funcionario':funcionario,
        'titulo':     f'Editar Funcionario: {funcionario.nombre_completo}',
        'boton':      'Guardar Cambios',
    })

#  SEDES

@login_required
@admin_required
def lista_sedes(request):
    hoy   = timezone.now().date()
    sedes = Sede.objects.filter(activa=True)
    sedes_data = [{'sede': s, 'ingresos_hoy': s.rendicion_dia(hoy)['total_ingresos']} for s in sedes]
    return render(request, 'sedes/listaSedes.html', {'sedes_data': sedes_data, 'fecha': hoy})

@login_required
@admin_required
def rendicion_sede(request, sede_id):
    sede      = get_object_or_404(Sede, pk=sede_id)
    fecha_str = request.GET.get('fecha')
    fecha     = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else timezone.now().date()
    rendicion = sede.rendicion_dia(fecha)
    return render(request, 'sedes/rendicionSedes.html', {
        'sede': sede, 'fecha': fecha, 'rendicion': rendicion,
        'pagos': rendicion['pagos'].select_related('alumno'),
    })


@login_required
@admin_required
def crear_sede(request):
    if request.method == 'POST':
        form = SedeForm(request.POST)
        if form.is_valid():
            sede = form.save()
            messages.success(request, f'Sede {sede.nombre} creada exitosamente.')
            return redirect('lista_sedes')
    else:
        form = SedeForm()
    return render(request, 'sedes/formSedes.html', {
        'form': form, 'titulo': 'Crear Nueva Sede', 'boton': 'Crear Sede',
    })

#  CONTEXT PROCESSOR — notificaciones

def notifications_processor(request):
    if not request.user.is_authenticated:
        return {'examenes_proximos': [], 'total_notificaciones': 0, 'solicitudes_pendientes_count': 0}

    hoy          = timezone.now().date()
    en_tres_dias = hoy + timedelta(days=3)

    parciales = Materia.objects.filter(
        fecha_examen_parcial__gte=hoy, fecha_examen_parcial__lte=en_tres_dias
    ).select_related('carrera')
    finales = Materia.objects.filter(
        fecha_examen_final__gte=hoy, fecha_examen_final__lte=en_tres_dias
    ).select_related('carrera')

    notificaciones = []
    for m in parciales:
        notificaciones.append({
            'tipo': 'Examen Parcial', 'materia': m.nombre, 'carrera': m.carrera.nombre,
            'carrera_id': m.carrera.id, 'fecha': m.fecha_examen_parcial,
            'icon': 'bi-calendar-event', 'color': 'text-primary',
        })
    for m in finales:
        notificaciones.append({
            'tipo': 'Examen Final', 'materia': m.nombre, 'carrera': m.carrera.nombre,
            'carrera_id': m.carrera.id, 'fecha': m.fecha_examen_final,
            'icon': 'bi-calendar-check', 'color': 'text-danger',
        })

    solicitudes_pendientes_count = 0
    if request.user.is_staff:
        solicitudes_objs = SolicitudEliminacion.objects.filter(estado='PENDIENTE').select_related('usuario_solicita')
        solicitudes_pendientes_count = solicitudes_objs.count()
        for s in solicitudes_objs:
            notificaciones.append({
                'id': f'solicitud_{s.id}', 'tipo': 'Solicitud de Eliminación',
                'materia': f'Solicitado por {s.usuario_solicita.username}',
                'carrera': s.get_modelo_display(), 'objeto_id': s.objeto_id,
                'motivo': s.motivo, 'datos_objeto': s.datos_objeto,
                'url_procesar': f'/procesar-solicitud-eliminacion/{s.id}/',
                'fecha': s.fecha_solicitud, 'icon': 'bi-trash', 'color': 'text-warning',
                'es_solicitud': True, 'solicitud_id': s.id,
            })

    notificaciones.sort(key=lambda x: x['fecha'].date() if isinstance(x['fecha'], datetime) else x['fecha'])
    return {
        'examenes_proximos':            notificaciones,
        'total_notificaciones':         len(notificaciones),
        'solicitudes_pendientes_count': solicitudes_pendientes_count,
    }

#  CARRERAS

@login_required
def lista_carreras(request):
    carreras      = Carrera.objects.filter(activa=True).prefetch_related('materias', 'alumnos')
    total_materias= sum(c.materias.count() for c in carreras)
    total_docentes= Funcionario.objects.filter(cargo='DOCENCIA', activo=True).count()
    return render(request, 'carreras/listaCarreras.html', {
        'carreras': carreras, 'total_materias': total_materias, 'total_docentes': total_docentes,
    })


@login_required
def detalle_carrera(request, carrera_id):
    carrera = get_object_or_404(Carrera, pk=carrera_id)
    return render(request, 'carreras/detalleCarrera.html', {
        'carrera':  carrera,
        'materias': carrera.materias.all().select_related('docente'),
        'docentes': Funcionario.objects.filter(cargo='DOCENCIA', activo=True),
    })


@login_required
def crear_carrera(request):
    if request.method == 'POST':
        form = CarreraForm(request.POST)
        if form.is_valid():
            carrera = form.save()
            messages.success(request, f'Carrera {carrera.nombre} creada exitosamente.')
            return redirect('detalle_carrera', carrera_id=carrera.id)
    else:
        form = CarreraForm()
    return render(request, 'carreras/formCarreras.html', {
        'form': form, 'titulo': 'Crear Nueva Carrera', 'boton': 'Crear Carrera',
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
        ultimo_orden = carrera.materias.aggregate(Max('orden'))['orden__max'] or 0
        form = MateriaForm(initial={'orden': ultimo_orden + 1})
    return render(request, 'carreras/formMaterias.html', {
        'form': form, 'carrera': carrera,
        'titulo': f'Agregar Materia a {carrera.nombre}', 'boton': 'Agregar Materia',
    })


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
    return render(request, 'carreras/formMaterias.html', {
        'form': form, 'materia': materia, 'carrera': materia.carrera,
        'titulo': f'Editar: {materia.nombre}', 'boton': 'Guardar Cambios',
    })


@login_required
def asignar_docente(request, materia_id):
    materia = get_object_or_404(Materia, pk=materia_id)
    if request.method == 'POST':
        docente_id = request.POST.get('docente_id')
        if docente_id:
            docente = get_object_or_404(Funcionario, pk=docente_id, cargo='DOCENCIA', activo=True)
            materia.docente = docente
            messages.success(request, f'Docente {docente.nombre_completo} asignado a {materia.nombre}.')
        else:
            materia.docente = None
            messages.info(request, f'Docente removido de {materia.nombre}.')
        materia.save()
        return redirect('detalle_carrera', carrera_id=materia.carrera.id)
    return render(request, 'carreras/asignarDocente.html', {
        'materia': materia,
        'docentes': Funcionario.objects.filter(cargo='DOCENCIA', activo=True),
        'carrera': materia.carrera,
    })


@login_required
def asignar_fechas(request, materia_id):
    materia = get_object_or_404(Materia, pk=materia_id)
    if request.method == 'POST':
        materia.fecha_examen_parcial = request.POST.get('fecha_examen_parcial') or None
        materia.fecha_examen_final   = request.POST.get('fecha_examen_final')   or None
        materia.save()
        messages.success(request, f'Fechas actualizadas para {materia.nombre}.')
        return redirect('detalle_carrera', carrera_id=materia.carrera.id)
    return render(request, 'carreras/asignarFechas.html', {
        'materia': materia, 'carrera': materia.carrera,
    })

#  USUARIOS

@login_required
@admin_required
def lista_usuarios(request):
    usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'usuarios/listaUsuarios.html', {
        'usuarios':        usuarios,
        'usuarios_activos':User.objects.filter(is_active=True).count(),
        'total_admin':     User.objects.filter(is_staff=True).count(),
        'total_estandar':  User.objects.filter(is_staff=False).count(),
    })


@login_required
@admin_required
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            if password := form.cleaned_data.get('password'):
                usuario.set_password(password)
            usuario.save()
            messages.success(request, f'Usuario {usuario.username} creado exitosamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm()
    return render(request, 'usuarios/formUsuarios.html', {
        'form': form, 'titulo': 'Crear Nuevo Usuario', 'boton': 'Crear Usuario',
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
        'form': form, 'usuario': usuario,
        'titulo': f'Editar Usuario: {usuario.username}', 'boton': 'Guardar Cambios',
    })


@login_required
@admin_required
def cambiar_estado_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    if usuario.is_superuser:
        messages.error(request, 'No puedes desactivar un superusuario.')
        return redirect('lista_usuarios')
    usuario.is_active = not usuario.is_active
    usuario.save()
    messages.success(request, f'Usuario {usuario.username} {"activado" if usuario.is_active else "desactivado"} exitosamente.')
    return redirect('lista_usuarios')


@login_required
def mi_perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect(request.POST.get('next') or 'mi_perfil')
    else:
        form = PerfilForm(instance=request.user)
    return render(request, 'usuarios/miPerfil.html', {'form': form, 'titulo': 'Mi Perfil'})


@login_required
def configuracion(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            update_session_auth_hash(request, form.save())
            messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
            return redirect(request.POST.get('next') or 'configuracion')
        else:
            messages.error(request, 'Por favor corrige los errores a continuación.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'usuarios/configuracion.html', {'form': form, 'titulo': 'Configuración'})

#  CAJA

@login_required
def lista_caja(request):
    hoy = timezone.now().date()

    # Filtros
    sede_id = request.GET.get('sede')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    recibo = request.GET.get('recibo')
    cliente = request.GET.get('cliente')

    # Base querysets
    ingresos = Pago.objects.all().select_related('alumno', 'sede', 'carrera').order_by('-fecha', '-id')
    egresos = Egreso.objects.all().select_related('sede').order_by('-fecha', '-id')

    # Calcular totales del DÍA DE HOY
    ingresos_hoy = ingresos.filter(fecha=hoy)
    egresos_hoy = egresos.filter(fecha=hoy)

    total_ingresos_hoy = ingresos_hoy.aggregate(Sum('importe_total'))['importe_total__sum'] or 0
    total_egresos_hoy = egresos_hoy.aggregate(Sum('monto'))['monto__sum'] or 0
    balance_hoy = total_ingresos_hoy - total_egresos_hoy

    # Aplicar filtros (para las tablas)
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

    # Calcular totales generales (con filtros aplicados)
    total_ingresos = ingresos.aggregate(Sum('importe_total'))['importe_total__sum'] or 0
    total_egresos = egresos.aggregate(Sum('monto'))['monto__sum'] or 0
    balance = total_ingresos - total_egresos

    # Limitar resultados
    ingresos = ingresos[:50]
    egresos = egresos[:50]

    sedes = Sede.objects.all().order_by('nombre')

    # Formatear fecha para mostrar
    fecha_hoy_formateada = hoy.strftime("%d/%m/%Y")
    fecha_hoy_param = hoy.strftime("%Y-%m-%d")

    context = {
        'ingresos': ingresos,
        'egresos': egresos,
        'ingresos_hoy': ingresos_hoy,
        'egresos_hoy': egresos_hoy,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': balance,
        'total_ingresos_hoy': total_ingresos_hoy,
        'total_egresos_hoy': total_egresos_hoy,
        'balance_hoy': balance_hoy,
        'fecha_hoy': fecha_hoy_formateada,
        'fecha_hoy_param': fecha_hoy_param,
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
def lista_egresos(request):
    egresos    = Egreso.objects.all().select_related('sede', 'usuario_registro').order_by('-fecha', '-id')
    sede_id    = request.GET.get('sede')
    categoria  = request.GET.get('categoria')
    fecha_desde= request.GET.get('fecha_desde')
    fecha_hasta= request.GET.get('fecha_hasta')

    if sede_id:     egresos = egresos.filter(sede_id=sede_id)
    if categoria:   egresos = egresos.filter(categoria=categoria)
    if fecha_desde: egresos = egresos.filter(fecha__gte=fecha_desde)
    if fecha_hasta: egresos = egresos.filter(fecha__lte=fecha_hasta)

    total_egresos = egresos.aggregate(Sum('monto'))['monto__sum'] or 0
    return render(request, 'caja/listaEgresos.html', {
        'egresos':        egresos[:100],
        'total_egresos':  total_egresos,
        'sedes':          Sede.objects.all().order_by('nombre'),
        'categorias':     Egreso.CATEGORIA_CHOICES,
        'filtros': {'sede': sede_id, 'categoria': categoria, 'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta},
    })


@login_required
def registrar_egreso(request):
    if request.method == 'POST':
        form = EgresoForm(request.POST, request.FILES)
        if form.is_valid():
            egreso = form.save(commit=False)
            egreso.usuario_registro = request.user
            egreso.save()
            comp = egreso.numero_comprobante
            if comp:
                messages.success(request, f'Egreso registrado exitosamente. Comprobante N° {comp}')
            else:
                messages.success(request, 'Egreso registrado exitosamente.')
            return redirect('detalle_egreso', egreso_uuid=egreso.uuid)
    else:
        form = EgresoForm()
    return render(request, 'caja/formEgreso.html', {'form': form, 'titulo': 'Registrar Egreso', 'boton': 'Registrar'})


@login_required
def detalle_egreso(request, egreso_uuid):
    egreso = get_object_or_404(Egreso.objects.select_related('sede', 'usuario_registro'), uuid=egreso_uuid)
    return render(request, 'caja/detalleEgreso.html', {'egreso': egreso})


@login_required
def editar_egreso(request, egreso_uuid):
    egreso = get_object_or_404(Egreso, uuid=egreso_uuid)
    if request.method == 'POST':
        form = EgresoForm(request.POST, request.FILES, instance=egreso)
        if form.is_valid():
            form.save()
            comp = egreso.numero_comprobante
            if comp:
                messages.success(request, f'Egreso actualizado exitosamente. Comprobante N° {comp}')
            else:
                messages.success(request, 'Egreso actualizado exitosamente.')
            return redirect('detalle_egreso', egreso_uuid=egreso.uuid)
    else:
        form = EgresoForm(instance=egreso)
    return render(request, 'caja/formEgreso.html', {'form': form, 'egreso': egreso, 'titulo': 'Editar Egreso', 'boton': 'Actualizar'})


@login_required
def eliminar_egreso(request, egreso_uuid):
    egreso = get_object_or_404(Egreso, uuid=egreso_uuid)
    if request.method == 'POST':
        if request.user.is_staff:
            comp = egreso.numero_comprobante
            egreso.delete()
            if comp:
                messages.success(request, f'Egreso con comprobante N° {comp} eliminado exitosamente.')
            else:
                messages.success(request, 'Egreso eliminado exitosamente.')
            return redirect('lista_egresos')
        else:
            SolicitudEliminacion.objects.create(
                usuario_solicita=request.user,
                modelo='EGRESO',
                objeto_id=egreso.id,
                motivo=request.POST.get('motivo', 'No especificado'),
                datos_objeto={'numero_comprobante': egreso.numero_comprobante, 'concepto': egreso.concepto, 'monto': str(egreso.monto), 'fecha': str(egreso.fecha)},
            )
            messages.info(request, 'Solicitud de eliminación enviada al administrador.')
            return redirect('detalle_egreso', egreso_uuid=egreso.uuid)
    return redirect('lista_egresos')

@login_required
def informe_caja(request):
    es_admin = request.user.is_staff

    sede_usuario = None
    if not es_admin:
        try:
            sede_usuario = request.user.perfil.sede
        except Exception:
            sede_usuario = None

        if sede_usuario is None:
            messages.error(
                request,
                'Tu usuario no tiene una sede asignada. '
                'Contactá al administrador para que te asigne una.'
            )
            return redirect('lista_caja')

    hoy = timezone.now().date()

    if es_admin:
        # ADMIN: puede usar rango de fechas
        fecha_desde_str = request.GET.get('fecha_desde')
        fecha_hasta_str = request.GET.get('fecha_hasta')

        if fecha_desde_str and fecha_hasta_str:
            try:
                fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
                fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                # Si hay error en las fechas, usar mes actual
                fecha_desde = hoy.replace(day=1)
                if hoy.month == 12:
                    fecha_hasta = hoy.replace(day=31)
                else:
                    fecha_hasta = (hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1))
        else:
            # Si no hay fechas, usar mes actual
            fecha_desde = hoy.replace(day=1)
            if hoy.month == 12:
                fecha_hasta = hoy.replace(day=31)
            else:
                fecha_hasta = (hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1))

        # Filtrar por sede para admin
        sede_id = request.GET.get('sede')
        sede_obj = get_object_or_404(Sede, id=sede_id) if sede_id else None

    else:
        # USUARIO COMÚN: puede seleccionar UNA fecha específica
        fecha_seleccionada_str = request.GET.get('fecha')

        if fecha_seleccionada_str:
            try:
                fecha_seleccionada = datetime.strptime(fecha_seleccionada_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                # Si hay error, usar hoy
                fecha_seleccionada = hoy
        else:
            # Si no hay fecha seleccionada, usar hoy
            fecha_seleccionada = hoy

        # Para usuarios comunes, la fecha desde y hasta son la misma
        fecha_desde = fecha_seleccionada
        fecha_hasta = fecha_seleccionada
        sede_obj = sede_usuario  # Sede forzada

    # Filtrar ingresos y egresos por fechas
    ingresos = Pago.objects.filter(
        fecha__gte=fecha_desde, fecha__lte=fecha_hasta
    )
    egresos = Egreso.objects.filter(
        fecha__gte=fecha_desde, fecha__lte=fecha_hasta
    )

    # Filtrar por sede si corresponde
    if sede_obj:
        ingresos = ingresos.filter(sede=sede_obj)
        egresos = egresos.filter(sede=sede_obj)

    # Ordenar y seleccionar relaciones
    ingresos = ingresos.select_related('alumno', 'sede', 'carrera').order_by('fecha')
    egresos = egresos.select_related('sede').order_by('fecha')

    # Calcular totales
    total_ingresos = ingresos.aggregate(Sum('importe_total'))['importe_total__sum'] or 0
    total_egresos = egresos.aggregate(Sum('monto'))['monto__sum'] or 0

    # Agrupar egresos por categoría
    egresos_por_categoria = {}
    for e in egresos:
        cat = e.get_categoria_display()
        egresos_por_categoria[cat] = egresos_por_categoria.get(cat, 0) + e.monto

    # Preparar contexto
    context = {
        'sede': sede_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'ingresos': ingresos,
        'egresos': egresos,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': total_ingresos - total_egresos,
        'egresos_por_categoria': egresos_por_categoria,
        'sedes': Sede.objects.all().order_by('nombre'),
        'es_admin': es_admin,
        'sede_forzada': None if es_admin else sede_usuario,
        'fecha_emision': timezone.now(),
        # Para usuarios comunes, pasar la fecha seleccionada
        'fecha_seleccionada': fecha_desde if not es_admin else None,
    }

    return render(request, 'caja/informeCaja.html', context)

#SOLICITUDES DE ELIMINACIÓN

@login_required
@admin_required
def lista_solicitudes_eliminacion(request):
    solicitudes = SolicitudEliminacion.objects.all().select_related('usuario_solicita').order_by('-fecha_solicitud')
    return render(request, 'usuarios/listaSolicitudesEliminacion.html', {
        'solicitudes': solicitudes,
        'pendientes':  solicitudes.filter(estado='PENDIENTE').count(),
    })


@login_required
@admin_required
def procesar_solicitud_eliminacion(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudEliminacion, id=solicitud_id)
    if request.method == 'POST':
        accion        = request.POST.get('accion')
        observaciones = request.POST.get('observaciones', '')
        solicitud.usuario_decide           = request.user
        solicitud.fecha_decision           = timezone.now()
        solicitud.observaciones_decision   = observaciones

        if accion == 'APROBAR':
            solicitud.estado = 'APROBADO'
            try:
                modelo_map = {
                    'PAGO': Pago, 'EGRESO': Egreso, 'ALUMNO': Alumno,
                    'CARRERA': Carrera, 'MATERIA': Materia,
                    'FUNCIONARIO': Funcionario, 'SEDE': Sede,
                }
                modelo_map[solicitud.modelo].objects.get(id=solicitud.objeto_id).delete()
                messages.success(request, 'Solicitud aprobada y objeto eliminado.')
            except Exception as e:
                messages.error(request, f'Error al eliminar el objeto: {str(e)}')
                solicitud.estado = 'PENDIENTE'
        else:
            solicitud.estado = 'RECHAZADO'
            messages.info(request, 'Solicitud de eliminación rechazada.')

        solicitud.save()
    return redirect('lista_solicitudes_eliminacion')

@login_required
def ficha_alumno(request, alumno_uuid):
    """
    Genera la ficha personal díptico del alumno.
    Calcula las 12 cuotas a partir de fecha_inicio y cruza con pagos reales.
    """
    alumno = get_object_or_404(Alumno, uuid=alumno_uuid)

    cuotas = []

    if alumno.fecha_inicio:
        pagos_alumno = alumno.pagos.filter(
            es_matricula=False
        ).exclude(fecha_vencimiento__isnull=True).order_by('fecha_vencimiento')

        for i in range(1, 13):
            vencimiento = alumno.fecha_inicio + relativedelta(months=i)

            rango_2_desde = vencimiento - timedelta(days=29)
            rango_2_hasta = vencimiento - timedelta(days=3)
            rango_1_desde = vencimiento - timedelta(days=2)
            rango_1_hasta = vencimiento + timedelta(days=5)

            ventana_desde = vencimiento - timedelta(days=15)
            ventana_hasta = vencimiento + timedelta(days=15)

            pago_cuota = pagos_alumno.filter(
                fecha_vencimiento__gte=ventana_desde,
                fecha_vencimiento__lte=ventana_hasta,
            ).first()

            if not pago_cuota:
                pago_cuota = pagos_alumno.filter(
                    numero_cuota__contains=str(i)
                ).first()

            cuotas.append({
                'numero':        i,
                'vencimiento':   vencimiento,
                'pago':          pago_cuota,
                'recibo':        pago_cuota.numero_recibo if pago_cuota else None,
                'fecha_pago':    pago_cuota.fecha         if pago_cuota else None,
                'puntaje':       pago_cuota.puntos        if pago_cuota else None,
                'rango_2_desde': rango_2_desde,
                'rango_2_hasta': rango_2_hasta,
                'rango_1_desde': rango_1_desde,
                'rango_1_hasta': rango_1_hasta,
            })

    cuotas_izq = cuotas[:6]
    cuotas_der = cuotas[6:]
    anio = alumno.fecha_inicio.year if alumno.fecha_inicio else timezone.now().year

    return render(request, 'alumnos/fichaAlumno.html', {
        'alumno':         alumno,
        'cuotas':         cuotas,
        'cuotas_izq':     cuotas_izq,
        'cuotas_der':     cuotas_der,
        'anio':           anio,
        'anio_siguiente': anio + 1,
        'tiene_inicio':   bool(alumno.fecha_inicio),
    })


@login_required
def editar_datos_ficha(request, alumno_uuid):
    """
    Recibe el POST del modo edición inline de fichaAlumno.html.
    Solo actualiza los campos del modelo Alumno que el JS envía:
    nombre, apellido, carrera, fecha_inicio, curso_actual.

    Los campos de institución (dirección, teléfono, etc.) se guardan
    en localStorage del navegador — no requieren modelo.
    """
    alumno = get_object_or_404(Alumno, uuid=alumno_uuid)

    if request.method == 'POST':
        # Campos directos del modelo
        nombre       = request.POST.get('nombre', '').strip()
        apellido     = request.POST.get('apellido', '').strip()
        fecha_inicio = request.POST.get('fecha_inicio', '').strip()
        curso_actual = request.POST.get('curso_actual', '').strip()
        carrera_id   = request.POST.get('carrera', '').strip()

        # Actualizar solo los campos que llegaron con valor
        if nombre:
            alumno.nombre = nombre
        if apellido:
            alumno.apellido = apellido

        # Carrera: validar que exista
        if carrera_id:
            try:
                from .models import Carrera
                alumno.carrera = Carrera.objects.get(pk=carrera_id)
            except (Carrera.DoesNotExist, ValueError):
                pass  # mantener la carrera actual si el id es inválido

        # Fecha de inicio: validar formato YYYY-MM-DD
        if fecha_inicio:
            from datetime import date
            try:
                año, mes, dia = fecha_inicio.split('-')
                alumno.fecha_inicio = date(int(año), int(mes), int(dia))
            except (ValueError, AttributeError):
                pass  # mantener fecha actual si el formato es inválido

        # Curso actual: entero o nulo
        if curso_actual:
            try:
                alumno.curso_actual = int(curso_actual)
            except ValueError:
                alumno.curso_actual = None
        else:
            alumno.curso_actual = None

        alumno.save()
        messages.success(request, 'Datos de la ficha actualizados correctamente.')

    # Siempre redirigir a la ficha (GET o POST)
    return redirect('ficha_alumno', alumno_uuid=alumno.uuid)
