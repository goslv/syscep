from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Sede, Carrera, Materia, Funcionario, AsistenciaFuncionario, Alumno, Pago, CanjeEstrellas, Egreso, \
    CuentaBancaria, PerfilUsuario


@admin.register(CanjeEstrellas)
class CanjeEstrellasAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'cantidad', 'concepto', 'fecha', 'usuario_registro']
    list_filter = ['fecha', 'usuario_registro']
    search_fields = ['alumno__nombre', 'alumno__apellido', 'concepto']
    readonly_fields = ['fecha', 'usuario_registro']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.usuario_registro = request.user
        super().save_model(request, obj, form, change)


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'activa', 'total_alumnos', 'total_funcionarios']
    list_filter = ['activa']
    search_fields = ['nombre', 'direccion']

    def total_alumnos(self, obj):
        return obj.alumnos.filter(activo=True).count()
    total_alumnos.short_description = 'Alumnos Activos'

    def total_funcionarios(self, obj):
        return obj.funcionarios.filter(activo=True).count()
    total_funcionarios.short_description = 'Funcionarios'


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'naturalidad', 'duracion_meses', 'activa', 'total_materias']
    list_filter = ['naturalidad', 'activa']
    search_fields = ['nombre']

    def total_materias(self, obj):
        return obj.materias.count()
    total_materias.short_description = 'Materias'


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'carrera', 'docente', 'bimestre', 'orden', 'tiene_classroom']
    list_filter = ['carrera', 'bimestre', 'docente']
    search_fields = ['nombre', 'carrera__nombre']
    ordering = ['carrera', 'orden']

    def tiene_classroom(self, obj):
        return "✓" if obj.link_classroom else "✗"
    tiene_classroom.short_description = 'Classroom'


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'cedula', 'cargo', 'sede', 'telefono_principal', 'activo']
    list_filter = ['cargo', 'sede', 'activo']
    search_fields = ['nombre', 'apellido', 'cedula']
    ordering = ['apellido', 'nombre']

    fieldsets = (
        ('Información Personal', {
            'fields': (('nombre', 'apellido'), 'cedula')
        }),
        ('Información Laboral', {
            'fields': (('sede', 'cargo'), 'fecha_ingreso', 'activo')
        }),
        ('Contacto', {
            'fields': (('telefono_principal', 'telefono_secundario'),)
        }),
    )

    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre Completo'
    nombre_completo.admin_order_field = 'apellido'


@admin.register(AsistenciaFuncionario)
class AsistenciaFuncionarioAdmin(admin.ModelAdmin):
    list_display = ['funcionario', 'fecha', 'presente_badge', 'observaciones']
    list_filter = ['fecha', 'presente', 'funcionario__cargo']
    search_fields = ['funcionario__nombre', 'funcionario__apellido']
    date_hierarchy = 'fecha'
    ordering = ['-fecha']

    def presente_badge(self, obj):
        if obj.presente:
            return format_html(
                '<span style="background-color:#28a745;color:white;padding:3px 10px;border-radius:3px;">✓ Presente</span>'
            )
        return format_html(
            '<span style="background-color:#dc3545;color:white;padding:3px 10px;border-radius:3px;">✗ Ausente</span>'
        )
    presente_badge.short_description = 'Estado'


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'cedula', 'carrera', 'sede', 'curso_actual',
                    'estado_pagos_display', 'total_puntos_display', 'activo']
    list_filter = ['carrera', 'sede', 'activo', 'curso_actual']
    search_fields = ['nombre', 'apellido', 'cedula']
    ordering = ['apellido', 'nombre']

    fieldsets = (
        ('Información Personal', {
            'fields': (('nombre', 'apellido'), 'cedula', 'fecha_nacimiento', 'telefono')
        }),
        ('Información Académica', {
            'fields': (('sede', 'carrera'), ('curso_actual', 'fecha_inicio'))
        }),
        ('Contacto de Emergencia', {
            'fields': ('contacto_emergencia_nombre',
                       ('contacto_emergencia_telefono', 'contacto_emergencia_relacion'))
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )

    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre Completo'
    nombre_completo.admin_order_field = 'apellido'

    def estado_pagos_display(self, obj):
        estado = obj.estado_pagos
        colores = {
            'AL_DIA': '#28a745',
            'CERCANO_VENCIMIENTO': '#ffc107',
            'ATRASADO': '#dc3545',
            'SIN_PAGOS': '#6c757d',
        }
        textos = {
            'AL_DIA': '✓ Al día',
            'CERCANO_VENCIMIENTO': '⚠ Por vencer',
            'ATRASADO': '✗ Atrasado',
            'SIN_PAGOS': '○ Sin pagos',
        }
        return format_html(
            '<span style="background-color:{};color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">{}</span>',
            colores.get(estado, '#6c757d'),
            textos.get(estado, estado)
        )
    estado_pagos_display.short_description = 'Estado de Pagos'

    def total_puntos_display(self, obj):
        # Renombrado de total_estrellas → total_puntos
        puntos = obj.total_puntos
        return format_html('<span style="font-size:16px;">★ {}</span>', puntos)
    total_puntos_display.short_description = 'Puntos'


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['numero_recibo', 'alumno_display', 'fecha', 'numero_cuota',
                    'importe_total_display', 'puntos_display', 'metodo_pago', 'es_matricula', 'sede']
    # ✅ Cambiado: 'estrellas' → 'puntos', agregado 'metodo_pago' y 'es_matricula'
    list_filter = ['fecha', 'sede', 'puntos', 'metodo_pago', 'es_matricula']
    search_fields = ['numero_recibo', 'alumno__nombre', 'alumno__apellido', 'recibido_de', 'nombre_cliente']
    date_hierarchy = 'fecha'
    # ✅ Cambiado: 'estrellas' → 'puntos'
    readonly_fields = ['puntos', 'fecha_creacion', 'preview_foto', 'preview_comprobante']
    ordering = ['-fecha', '-fecha_creacion']

    fieldsets = (
        ('Información del Recibo', {
            'fields': ('numero_recibo', 'foto_recibo', 'preview_foto',
                       'foto_comprobante', 'preview_comprobante', 'sede', 'alumno', 'carrera')
        }),
        ('Tipo y Método de Pago', {
            # ✅ Nuevo fieldset con los campos nuevos
            'fields': (('es_matricula', 'metodo_pago'),)
        }),
        ('Datos del Pago', {
            'fields': (('fecha', 'recibido_de'), 'suma_de', 'concepto', 'curso', 'nombre_cliente')
        }),
        ('Detalles de la Cuota', {
            'fields': (('numero_cuota', 'fecha_vencimiento'),
                       'valido_hasta', 'importe_total', 'monto_unitario', 'cantidad_cuotas')
        }),
        ('Información Adicional', {
            # ✅ Cambiado: 'estrellas' → 'puntos'
            'fields': ('recibido_por', 'usuario_registro', 'observaciones', ('puntos', 'fecha_creacion'))
        }),
    )

    def alumno_display(self, obj):
        if obj.alumno:
            return obj.alumno.nombre_completo
        if obj.nombre_cliente:
            return obj.nombre_cliente
        return "Sin especificar"
    alumno_display.short_description = 'Alumno'
    alumno_display.admin_order_field = 'alumno__apellido'

    def importe_total_display(self, obj):
        return format_html(
            '<strong>Gs. {:,.0f}</strong>', obj.importe_total
        ).replace(',', '.')
    importe_total_display.short_description = 'Importe Total'
    importe_total_display.admin_order_field = 'importe_total'

    def puntos_display(self, obj):
        # ✅ Renombrado de estrellas_display → puntos_display
        if obj.puntos == 0:
            return format_html('<span style="color:#999;">—</span>')
        colores = {3: '#FFD700', 2: '#C0C0C0', 1: '#CD7F32'}
        color = colores.get(obj.puntos, '#999')
        return format_html(
            '<span style="font-size:18px;color:{};">★ {}</span>',
            color, obj.puntos
        )
    puntos_display.short_description = 'Puntos'

    def preview_foto(self, obj):
        if obj.foto_recibo:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width:200px;max-height:200px;border:1px solid #ddd;border-radius:4px;padding:5px;"/></a>',
                obj.foto_recibo.url, obj.foto_recibo.url
            )
        return "No hay foto"
    preview_foto.short_description = 'Vista Previa Recibo'

    def preview_comprobante(self, obj):
        if obj.foto_comprobante:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width:200px;max-height:200px;border:1px solid #ddd;border-radius:4px;padding:5px;"/></a>',
                obj.foto_comprobante.url, obj.foto_comprobante.url
            )
        return "No hay comprobante"
    preview_comprobante.short_description = 'Vista Previa Comprobante'


@admin.register(Egreso)
class EgresoAdmin(admin.ModelAdmin):
    list_display = ['numero_comprobante', 'fecha', 'categoria', 'monto_display', 'sede', 'usuario_registro']
    list_filter = ['fecha', 'categoria', 'sede']
    search_fields = ['numero_comprobante', 'concepto', 'observaciones']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha_creacion', 'preview_comprobante']

    def monto_display(self, obj):
        return format_html(
            '<strong>Gs. {:,.0f}</strong>', obj.monto
        ).replace(',', '.')
    monto_display.short_description = 'Monto'
    monto_display.admin_order_field = 'monto'

    def preview_comprobante(self, obj):
        if obj.comprobante:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width:200px;max-height:200px;border:1px solid #ddd;border-radius:4px;padding:5px;"/></a>',
                obj.comprobante.url, obj.comprobante.url
            )
        return "No hay comprobante"
    preview_comprobante.short_description = 'Vista Previa'

    fieldsets = (
        ('Información Básica', {
            # ✅ numero_comprobante ahora es opcional, sin asterisco implícito
            'fields': ('sede', 'numero_comprobante', 'fecha', 'categoria')
        }),
        ('Detalles del Gasto', {
            'fields': ('concepto', 'monto')
        }),
        ('Soporte', {
            'fields': ('comprobante', 'preview_comprobante')
        }),
        ('Registro', {
            'fields': ('usuario_registro', 'observaciones', 'fecha_creacion')
        }),
    )

@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ['entidad', 'titular', 'activa', 'fecha_creacion']
    list_filter  = ['activa']
    search_fields = ['entidad', 'titular']

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display  = ['user', 'sede']
    list_filter   = ['sede']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
    autocomplete_fields = ['sede']

class PerfilInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'
class UserAdminExtendido(UserAdmin):
    inlines = [PerfilInline]

admin.site.unregister(User)
admin.site.register(User, UserAdminExtendido)

# Personalización del sitio admin
admin.site.site_header = "CEP Admin - Sistema Administrativo CEP"
admin.site.site_title = "CEP Admin"
admin.site.index_title = "Panel de Administración"

