from typing import Any

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

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
        """Retorna la rendición del día para esta sede"""
        if fecha is None:
            fecha = timezone.now().date()
        pagos = self.pagos.filter(fecha=fecha)
        return {
            'total': pagos.aggregate(models.Sum('importe_total'))['importe_total__sum'] or 0,
            'cantidad_pagos': pagos.count(),
            'pagos': pagos
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
    activa = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_naturalidad_display()})"

    def get_naturalidad_display(self):
        pass


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

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(args, kwargs)
        self.asistencias = None

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.get_cargo_display()}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def asistencias_mes(self, mes=None, anio=None):
        """Retorna las asistencias del mes especificado"""
        if mes is None:
            mes = timezone.now().month
        if anio is None:
            anio = timezone.now().year
        return self.asistencias.filter(fecha__month=mes, fecha__year=anio)

    def get_cargo_display(self):
        pass


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
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='alumnos', verbose_name="Sede")
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT, related_name='alumnos', verbose_name="Carrera")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    curso_actual = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Curso Actual")

    # Contacto de emergencia
    contacto_emergencia_nombre = models.CharField(max_length=200, verbose_name="Contacto de Emergencia")
    contacto_emergencia_telefono = models.CharField(max_length=20, verbose_name="Teléfono de Emergencia")
    contacto_emergencia_relacion = models.CharField(max_length=100, verbose_name="Relación")

    activo = models.BooleanField(default=True, verbose_name="Activo")
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
        """Determina el estado de pagos del alumno"""
        ultimo_pago = self.pagos.order_by('-fecha_vencimiento').first()

        if not ultimo_pago:
            return 'SIN_PAGOS'

        hoy = timezone.now().date()
        diferencia = (ultimo_pago.fecha_vencimiento - hoy).days

        if diferencia >= 0:
            return 'AL_DIA'
        elif diferencia >= -3:
            return 'CERCANO_VENCIMIENTO'
        else:
            return 'ATRASADO'

    @property
    def puede_rendir_examen(self):
        """Verifica si el alumno puede rendir examen (debe estar al día)"""
        return self.estado_pagos in ['AL_DIA', 'CERCANO_VENCIMIENTO']

    @property
    def total_estrellas(self):
        """Calcula el total de estrellas acumuladas"""
        return self.pagos.aggregate(models.Sum('estrellas'))['estrellas__sum'] or 0


class Pago(models.Model):
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='pagos', verbose_name="Sede")
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='pagos', verbose_name="Alumno")

    numero_recibo = models.CharField(max_length=50, unique=True, verbose_name="Nº de Recibo")
    foto_recibo = models.ImageField(upload_to='recibos/%Y/%m/', blank=True, null=True, verbose_name="Foto del Recibo")

    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    recibido_de = models.CharField(max_length=200, verbose_name="Recibido de")
    suma_de = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="La suma de")
    concepto = models.TextField(verbose_name="En concepto de")
    curso = models.CharField(max_length=100, verbose_name="Curso")

    valido_hasta = models.DateField(null=True, blank=True, verbose_name="Válido hasta")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    numero_cuota = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Nº de Cuota")

    importe_parcial = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Importe Parcial")
    importe_total = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Importe Total")

    recibido_por = models.CharField(max_length=200, verbose_name="Recibido por")

    # Sistema de estrellas (se calcula automáticamente)
    estrellas = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Estrellas")

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    foto_comprobante = models.ImageField(upload_to='comprobantes/', blank=True, null=True)

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
        ordering = ['-fecha', '-numero_cuota']
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"Recibo {self.numero_recibo} - {self.alumno.nombre_completo} - Cuota {self.numero_cuota}"

    def calcular_estrellas(self):
        """Calcula las estrellas según la fecha de pago vs vencimiento"""
        # Si no hay fecha de vencimiento, retornar 0
        if not self.fecha_vencimiento:
            return 0

        diferencia = (self.fecha_vencimiento - self.fecha).days
        if diferencia >= 30:
            return 3  # Pago 1 mes antes
        elif diferencia >= 3:
            return 2  # Pago 3 días antes o más
        elif diferencia >= -3:
            return 1  # Hasta 3 días después
        else:
            return 0  # Más de 3 días atrasado

    def save(self, *args, **kwargs):
        """Calcula automáticamente las estrellas al guardar"""
        if not self.pk:  # Solo para pagos nuevos
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

    def __str__(self):
        return f"Pago {self.numero_recibo} - {self.nombre_pagador}"

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'


class Max:
    pass