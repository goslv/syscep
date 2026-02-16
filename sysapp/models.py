import os
import uuid
from typing import Any

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


def path_comprobante_pago(instance, filename):
    # Extension del archivo
    ext = filename.split('.')[-1]
    # Nombre del archivo basado en la fecha o id si no hay fecha
    fecha_str = instance.fecha.strftime('%d-%m-%Y') if instance.fecha else timezone.now().strftime('%d-%m-%Y')
    # Carpeta: Comprobantes/Ingreso/DD-MM-YYYY/
    return os.path.join('Comprobantes', 'Ingreso', fecha_str, filename)


def path_comprobante_egreso(instance, filename):
    # Extension del archivo
    ext = filename.split('.')[-1]
    # Nombre del archivo basado en la fecha o id si no hay fecha
    fecha_str = instance.fecha.strftime('%d-%m-%Y') if instance.fecha else timezone.now().strftime('%d-%m-%Y')
    # Categoría del egreso
    categoria = instance.categoria if hasattr(instance, 'categoria') else 'OTROS'
    # Carpeta: Comprobantes/Egreso/CATEGORIA/DD-MM-YYYY/
    return os.path.join('Comprobantes', 'Egreso', categoria, fecha_str, filename)


class Sede(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    direccion = models.TextField(verbose_name="Dirección")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def rendicion_dia(self, fecha=None):
        if fecha is None:
            fecha = timezone.now().date()

        # Ingresos (Pagos)
        pagos = self.pagos.filter(fecha=fecha)
        total_ingresos = pagos.aggregate(models.Sum('importe_total'))['importe_total__sum'] or 0

        # Egresos
        egresos = self.egresos.filter(fecha=fecha)
        total_egresos = egresos.aggregate(models.Sum('monto'))['monto__sum'] or 0

        # Balance
        balance = total_ingresos - total_egresos

        return {
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'balance': balance,
            'cantidad_pagos': pagos.count(),
            'cantidad_egresos': egresos.count(),
            'pagos': pagos,
            'egresos': egresos
        }


class Carrera(models.Model):
    NATURALIDAD_CHOICES = [
        ('TS', 'Técnico Superior'),
        ('FP', 'Formación Profesional'),
    ]

    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    naturalidad = models.CharField(max_length=2, choices=NATURALIDAD_CHOICES, verbose_name="Tipo")
    duracion_meses = models.IntegerField(help_text="Duración total en meses", verbose_name="Duración (meses)")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    monto_matricula = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name="Monto Matrícula (Gs.)",
        help_text="Costo de matrícula de la carrera"
    )
    monto_mensualidad = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name="Mensualidad (Gs.)",
        help_text="Costo mensual de la carrera"
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_naturalidad_display()})"


class Materia(models.Model):
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='materias', verbose_name="Carrera")
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    link_classroom = models.URLField(blank=True, help_text="Link de Google Classroom", verbose_name="Link Classroom")
    bimestre = models.IntegerField(null=True, blank=True, help_text="Solo para Técnico Superior",
                                   verbose_name="Bimestre")
    orden = models.IntegerField(default=0, help_text="Orden de la materia en el plan", verbose_name="Orden")
    docente = models.ForeignKey('Funcionario', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='materias_asignadas', verbose_name="Docente",
                                limit_choices_to={'cargo': 'DOCENCIA', 'activo': True})

    # EXÁMENES
    fecha_examen_parcial = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Examen Parcial",
        help_text="Fecha del examen parcial de la materia"
    )
    fecha_examen_final = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Examen Final",
        help_text="Fecha del examen final de la materia"
    )

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        ordering = ['carrera', 'orden']

    def __str__(self):
        bimestre_info = f" - Bim. {self.bimestre}" if self.bimestre else ""
        return f"{self.carrera.nombre}: {self.nombre}{bimestre_info}"


class Funcionario(models.Model):
    CARGO_CHOICES = [
        ('DOCENCIA', 'Docencia'),
        ('ADMINISTRATIVO', 'Administrativo'),
        ('DIRECCION', 'Dirección'),
        ('OTRO', 'Otro'),
    ]

    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='funcionarios', verbose_name="Sede")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula")
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES, verbose_name="Cargo")
    telefono_principal = models.CharField(max_length=20, verbose_name="Teléfono Principal")
    telefono_secundario = models.CharField(max_length=20, blank=True, verbose_name="Teléfono Secundario")
    fecha_ingreso = models.DateField(verbose_name="Fecha de Ingreso")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Funcionario"
        verbose_name_plural = "Funcionarios"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.get_cargo_display()}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def asistencias_mes(self, mes=None, anio=None):
        if mes is None:
            mes = timezone.now().month
        if anio is None:
            anio = timezone.now().year
        return self.asistencias.filter(fecha__month=mes, fecha__year=anio)


class AsistenciaFuncionario(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='asistencias',
                                    verbose_name="Funcionario")
    fecha = models.DateField(verbose_name="Fecha")
    presente = models.BooleanField(default=True, verbose_name="Presente")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Asistencia de Funcionario"
        verbose_name_plural = "Asistencias de Funcionarios"
        unique_together = ['funcionario', 'fecha']
        ordering = ['-fecha']

    def __str__(self):
        estado = 'Presente' if self.presente else 'Ausente'
        return f"{self.funcionario.nombre_completo} - {self.fecha} - {estado}"


class Alumno(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # CAMPOS OBLIGATORIOS
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='alumnos')
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='alumnos')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    # CAMPOS OPCIONALES - Información personal
    cedula = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    curso_actual = models.IntegerField(blank=True, null=True)

    # CAMPOS OPCIONALES - Contacto de emergencia
    contacto_emergencia_nombre = models.CharField(max_length=100, blank=True, null=True)
    contacto_emergencia_telefono = models.CharField(max_length=20, blank=True, null=True)
    contacto_emergencia_relacion = models.CharField(max_length=50, blank=True, null=True)

    # CAMPOS DE ESTADO
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.carrera.nombre}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def estado_pagos(self):
        # Obtener el último pago registrado
        ultimo_pago = self.pagos.order_by('-fecha_vencimiento').first()

        # Si no hay pagos registrados
        if not ultimo_pago:
            return 'SIN_PAGOS'

        # Si el pago no tiene fecha de vencimiento, se considera sin información suficiente
        if not ultimo_pago.fecha_vencimiento:
            return 'SIN_FECHA_VENCIMIENTO'

        # Calcular la diferencia de días
        hoy = timezone.now().date()
        try:
            diferencia = (ultimo_pago.fecha_vencimiento - hoy).days
        except (TypeError, AttributeError):
            # Por seguridad adicional, en caso de cualquier error en la resta
            return 'ERROR_FECHA'

        # Determinar el estado según los días de diferencia
        if diferencia >= 0:
            return 'AL_DIA'
        elif diferencia >= -3:
            return 'CERCANO_VENCIMIENTO'
        else:
            return 'ATRASADO'

    @property
    def dias_hasta_vencimiento(self):
        ultimo_pago = self.pagos.order_by('-fecha_vencimiento').first()

        if not ultimo_pago or not ultimo_pago.fecha_vencimiento:
            return None

        hoy = timezone.now().date()
        try:
            return (ultimo_pago.fecha_vencimiento - hoy).days
        except (TypeError, AttributeError):
            return None

    @property
    def puede_rendir_examen(self):
        estado = self.estado_pagos
        return estado in ['AL_DIA', 'CERCANO_VENCIMIENTO']

    @property
    def total_estrellas(self):
        acumuladas = self.pagos.aggregate(models.Sum('estrellas'))['estrellas__sum'] or 0
        canjeadas = self.canjes.aggregate(models.Sum('cantidad'))['cantidad__sum'] or 0
        return acumuladas - canjeadas

    def obtener_detalle_estado_pagos(self):
        ultimo_pago = self.pagos.order_by('-fecha_vencimiento').first()

        detalle = {
            'estado': self.estado_pagos,
            'tiene_pagos': ultimo_pago is not None,
            'ultimo_pago': ultimo_pago,
            'dias_hasta_vencimiento': self.dias_hasta_vencimiento,
            'puede_rendir': self.puede_rendir_examen,
        }

        if detalle['estado'] == 'SIN_PAGOS':
            detalle['mensaje'] = 'El alumno no tiene pagos registrados'
        elif detalle['estado'] == 'SIN_FECHA_VENCIMIENTO':
            detalle['mensaje'] = 'El último pago no tiene fecha de vencimiento'
        elif detalle['estado'] == 'AL_DIA':
            detalle['mensaje'] = 'Pagos al día'
        elif detalle['estado'] == 'CERCANO_VENCIMIENTO':
            detalle['mensaje'] = f'Vence en {abs(detalle["dias_hasta_vencimiento"])} días'
        elif detalle['estado'] == 'ATRASADO':
            detalle['mensaje'] = f'Atrasado por {abs(detalle["dias_hasta_vencimiento"])} días'
        else:
            detalle['mensaje'] = 'Estado desconocido'

        return detalle


class Pago(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='pagos', verbose_name="Sede")
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='pagos',
                               verbose_name="Alumno", null=True, blank=True)
    carrera = models.ForeignKey(Carrera, on_delete=models.SET_NULL, related_name='pagos',
                                verbose_name="Carrera", null=True, blank=True)

    numero_recibo = models.CharField(max_length=50, unique=True, null=True, blank=True,
                                     verbose_name="Nº de Recibo")
    foto_recibo = models.ImageField(upload_to=path_comprobante_pago, blank=True, null=True,
                                    verbose_name="Foto del Recibo")

    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    recibido_de = models.CharField(max_length=200, verbose_name="Recibido de", blank=True, null=True)
    suma_de = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="La suma de",
                                  blank=True, null=True)
    concepto = models.TextField(verbose_name="En concepto de")
    curso = models.CharField(max_length=100, verbose_name="Curso", blank=True, null=True)

    valido_hasta = models.DateField(null=True, blank=True, verbose_name="Válido hasta")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento", null=True, blank=True)
    numero_cuota = models.CharField(max_length=50, verbose_name="Nº de Cuota",
                                    null=True, blank=True,
                                    help_text="Ej: 1 o 3,4,5")

    importe_total = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Importe Total")

    recibido_por = models.CharField(max_length=200, verbose_name="Recibido por", blank=True, null=True)

    # Sistema de puntos (se calcula automáticamente)
    estrellas = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Estrellas")

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    foto_comprobante = models.ImageField(upload_to=path_comprobante_pago, blank=True, null=True)

    observaciones = models.TextField(blank=True, null=True)

    nombre_cliente = models.CharField(max_length=200, null=True, blank=True,
                                      help_text='Nombre del cliente si no es alumno regular')
    validez_pago = models.DateField(null=True, blank=True,
                                    help_text='Fecha de validez del pago')
    monto_unitario = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True,
                                         help_text='Monto por cada cuota')
    cantidad_cuotas = models.IntegerField(null=True, blank=True, default=1,
                                          help_text='Cantidad de cuotas pagadas')
    usuario_registro = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         help_text='Usuario que registró el pago')

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        numero = self.numero_recibo or "Sin recibo"
        return f"Pago {numero} - {self.nombre_pagador}"

    def calcular_estrellas(self):
        # Si no hay fecha de vencimiento, retornar 0
        if not self.fecha_vencimiento:
            return 0

        # Si no hay fecha de pago, usar la fecha actual
        fecha_pago = self.fecha if self.fecha else timezone.now().date()

        try:
            diferencia = (self.fecha_vencimiento - fecha_pago).days
        except (TypeError, AttributeError):
            # En caso de error en el cálculo, retornar 0
            return 0

        # Asignar estrellas según la anticipación del pago
        if diferencia >= 30:
            return 3  # Pago 1 mes antes o más
        elif diferencia >= 3:
            return 2  # Pago 3 días antes o más
        elif diferencia >= -3:
            return 1  # Hasta 3 días después
        else:
            return 0  # Más de 3 días atrasado

    def save(self, *args, **kwargs):
        # Calcular estrellas solo para pagos nuevos o si las estrellas están en 0
        if not self.pk or self.estrellas == 0:
            self.estrellas = self.calcular_estrellas()
        super().save(*args, **kwargs)

    @property
    def es_cliente_diferenciado(self):
        """Indica si el pago es de un cliente diferenciado"""
        return self.nombre_cliente is not None and self.nombre_cliente != ''

    @property
    def nombre_pagador(self):
        """Retorna el nombre del alumno o del cliente diferenciado"""
        if self.es_cliente_diferenciado:
            return self.nombre_cliente
        elif self.alumno:
            return self.alumno.nombre_completo
        return 'Sin especificar'

    @property
    def dias_para_vencimiento(self):
        """
        NUEVO: Retorna los días que faltan para el vencimiento
        Valores negativos indican días de atraso
        """
        if not self.fecha_vencimiento:
            return None

        try:
            hoy = timezone.now().date()
            return (self.fecha_vencimiento - hoy).days
        except (TypeError, AttributeError):
            return None

    @property
    def esta_vencido(self):
        """NUEVO: Indica si el pago está vencido"""
        dias = self.dias_para_vencimiento
        return dias is not None and dias < 0

class CanjeEstrellas(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='canjes', verbose_name="Alumno")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad de Estrellas")
    concepto = models.CharField(max_length=200, verbose_name="Concepto/Premio")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Canje")
    usuario_registro = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Canje de Estrellas"
        verbose_name_plural = "Canjes de Estrellas"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.alumno.nombre_completo} - {self.cantidad} ⭐ - {self.concepto}"

    def save(self, *args, **kwargs):
        """
        MEJORADO: Valida que el alumno tenga suficientes estrellas antes de canjear
        """
        if not self.pk:  # Solo para canjes nuevos
            estrellas_disponibles = self.alumno.total_estrellas
            if estrellas_disponibles < self.cantidad:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"El alumno solo tiene {estrellas_disponibles} estrellas disponibles. "
                    f"No puede canjear {self.cantidad} estrellas."
                )
        super().save(*args, **kwargs)


class Egreso(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    CATEGORIA_CHOICES = [
        ('SERVICIOS', 'Servicios (Luz, Agua, Internet)'),
        ('SUELDOS', 'Sueldos y Salarios'),
        ('MATERIALES', 'Materiales y Suministros'),
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('ALQUILER', 'Alquiler'),
        ('IMPUESTOS', 'Impuestos y Tasas'),
        ('OTROS', 'Otros Gastos'),
    ]

    sede = models.ForeignKey(
        Sede,
        on_delete=models.CASCADE,
        related_name='egresos',
        verbose_name="Sede"
    )
    numero_comprobante = models.CharField(
        max_length=50,
        verbose_name="Nº de Comprobante",
        help_text="Número de factura o comprobante"
    )
    fecha = models.DateField(
        default=timezone.now,
        verbose_name="Fecha"
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name="Categoría"
    )
    concepto = models.TextField(
        verbose_name="Concepto",
        help_text="Descripción detallada del gasto"
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name="Monto (Gs.)",
        validators=[MinValueValidator(0)]
    )
    comprobante = models.ImageField(
        upload_to=path_comprobante_egreso,
        blank=True,
        null=True,
        verbose_name="Comprobante"
    )
    usuario_registro = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Registrado por"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = "Egreso"
        verbose_name_plural = "Egresos"

    def __str__(self):
        return f"Egreso {self.numero_comprobante} - {self.concepto[:30]} - Gs. {self.monto:,.0f}"

    def clean(self):
        """
        NUEVO: Validación adicional para asegurar datos correctos
        """
        from django.core.exceptions import ValidationError

        if self.monto and self.monto < 0:
            raise ValidationError({'monto': 'El monto no puede ser negativo'})

        if not self.numero_comprobante or not self.numero_comprobante.strip():
            raise ValidationError({'numero_comprobante': 'El número de comprobante es obligatorio'})


class SolicitudEliminacion(models.Model):
    MODELO_CHOICES = [
        ('PAGO', 'Pago'),
        ('EGRESO', 'Egreso'),
        ('ALUMNO', 'Alumno'),
        ('CARRERA', 'Carrera'),
        ('MATERIA', 'Materia'),
        ('FUNCIONARIO', 'Funcionario'),
        ('SEDE', 'Sede'),
    ]

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    usuario_solicita = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='solicitudes_eliminacion')
    modelo = models.CharField(max_length=20, choices=MODELO_CHOICES)
    objeto_id = models.PositiveIntegerField()
    motivo = models.TextField(verbose_name="Motivo de la eliminación")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE')
    usuario_decide = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='decisiones_eliminacion')
    fecha_decision = models.DateTimeField(null=True, blank=True)
    observaciones_decision = models.TextField(blank=True, null=True)
    datos_objeto = models.JSONField(help_text="Copia de los datos del objeto para mostrar en la notificación",
                                    null=True, blank=True)

    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name = "Solicitud de Eliminación"
        verbose_name_plural = "Solicitudes de Eliminación"

    def __str__(self):
        return f"Solicitud de {self.usuario_solicita.username} - {self.get_modelo_display()} (ID: {self.objeto_id})"

    def aprobar(self, usuario, observaciones=''):
        self.estado = 'APROBADO'
        self.usuario_decide = usuario
        self.fecha_decision = timezone.now()
        self.observaciones_decision = observaciones
        self.save()

    def rechazar(self, usuario, observaciones=''):
        self.estado = 'RECHAZADO'
        self.usuario_decide = usuario
        self.fecha_decision = timezone.now()
        self.observaciones_decision = observaciones
        self.save()