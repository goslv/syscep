from django import forms
from django.contrib.auth.models import User

from .models import (
    Pago, Alumno, Funcionario, AsistenciaFuncionario,
    Sede, Carrera, Materia, Egreso, CuentaBancaria,
)


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False, label='Contraseña',
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False, label='Confirmar Contraseña',
    )
    sede = forms.ModelChoiceField(
        queryset=None, required=False, label='Sede asignada',
        empty_label='Sin restricción (acceso global)',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'is_staff':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Sede
        self.fields['sede'].queryset = Sede.objects.filter(activa=True).order_by('nombre')
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True
        else:
            try:
                self.initial['sede'] = self.instance.perfil.sede
            except Exception:
                pass

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password or password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Las contraseñas no coinciden.')
            if len(password) < 8:
                raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if password := self.cleaned_data.get('password'):
            user.set_password(password)
        if commit:
            user.save()
            from .models import PerfilUsuario
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.sede = self.cleaned_data.get('sede')
            perfil.save()
        return user


class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
        }


# ══════════════════════════════════════════════════════════════════════════
#  PAGO FORM
# ══════════════════════════════════════════════════════════════════════════
class PagoForm(forms.ModelForm):
    es_matricula = forms.BooleanField(
        required=False, label='Es Matrícula',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_es_matricula'})
    )
    metodo_pago = forms.ChoiceField(
        choices=Pago.METODO_PAGO_CHOICES, initial='EFECTIVO', label='Método de Pago',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    es_cliente_diferenciado = forms.BooleanField(
        required=False, label='Cliente no regular',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    nombre_cliente = forms.CharField(
        required=False, max_length=200, label='Nombre del Cliente',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo del cliente'})
    )
    carrera_otro = forms.CharField(
        required=False, max_length=200, label='Especificar carrera o curso',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_carrera_otro', 'placeholder': 'Ej: Inglés avanzado…'})
    )
    validez_pago = forms.DateField(
        required=False, label='Validez del Pago',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_vencimiento = forms.DateField(
        required=False, label='Fecha de Vencimiento',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    monto_unitario = forms.DecimalField(
        required=False, max_digits=10, decimal_places=0, label='Monto Unitario (Gs.)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'})
    )
    cantidad_cuotas = forms.IntegerField(
        required=False, label='Cantidad de Cuotas',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'})
    )

    class Meta:
        model = Pago
        fields = [
            'numero_recibo', 'fecha', 'alumno', 'sede', 'carrera',
            'numero_cuota', 'concepto', 'importe_total', 'puntos',
            'foto_comprobante', 'observaciones', 'es_matricula', 'metodo_pago',
        ]
        widgets = {
            'numero_recibo':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'fecha':            forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'alumno':           forms.Select(attrs={'class': 'form-select'}),
            'sede':             forms.Select(attrs={'class': 'form-select', 'required': True}),
            'carrera':          forms.Select(attrs={'class': 'form-select', 'id': 'id_carrera'}),
            'numero_cuota':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional. Ej: 3,4,5'}),
            'puntos':           forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'concepto':         forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'importe_total':    forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'foto_comprobante': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'observaciones':    forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['alumno'].queryset  = Alumno.objects.all().order_by('apellido', 'nombre')
        self.fields['sede'].queryset    = Sede.objects.all().order_by('nombre')
        self.fields['carrera'].queryset = Carrera.objects.filter(activa=True).order_by('nombre')
        for f in ['numero_recibo', 'alumno', 'carrera', 'observaciones', 'foto_comprobante', 'puntos', 'carrera_otro']:
            self.fields[f].required = False
        if self.instance.pk:
            self.initial['es_matricula'] = self.instance.es_matricula
            self.initial['metodo_pago']  = self.instance.metodo_pago or 'EFECTIVO'
            if self.instance.carrera:
                self.initial['carrera'] = self.instance.carrera
            elif self.instance.alumno:
                self.initial['carrera'] = self.instance.alumno.carrera
            if self.instance.monto_unitario is not None:
                self.initial['monto_unitario'] = self.instance.monto_unitario
            if self.instance.cantidad_cuotas is not None:
                self.initial['cantidad_cuotas'] = self.instance.cantidad_cuotas
            if self.instance.nombre_cliente:
                self.initial['es_cliente_diferenciado'] = True
                self.initial['nombre_cliente'] = self.instance.nombre_cliente

    def clean(self):
        cleaned_data    = super().clean()
        es_cliente_dif  = cleaned_data.get('es_cliente_diferenciado')
        es_matricula    = cleaned_data.get('es_matricula')
        alumno          = cleaned_data.get('alumno')
        carrera         = cleaned_data.get('carrera')
        nombre_cliente  = cleaned_data.get('nombre_cliente')
        cantidad_cuotas = cleaned_data.get('cantidad_cuotas') or 1
        monto_unitario  = cleaned_data.get('monto_unitario')
        importe_total   = cleaned_data.get('importe_total')

        if es_cliente_dif:
            if not nombre_cliente:
                raise forms.ValidationError('Debe ingresar el nombre del cliente.')
            cleaned_data['alumno'] = None
        else:
            if not alumno:
                raise forms.ValidationError('Debe seleccionar un alumno.')

        if not carrera and alumno:
            cleaned_data['carrera'] = alumno.carrera
            carrera = alumno.carrera

        if es_matricula:
            if not monto_unitario and carrera:
                cleaned_data['monto_unitario'] = carrera.monto_matricula
                monto_unitario = carrera.monto_matricula
            cleaned_data['cantidad_cuotas']    = 1
            cleaned_data['puntos']             = 0
            cleaned_data['fecha_vencimiento']  = None
            cleaned_data['numero_cuota']       = None
        else:
            if not monto_unitario and carrera:
                cleaned_data['monto_unitario'] = carrera.monto_mensualidad
                monto_unitario = carrera.monto_mensualidad
            cleaned_data['cantidad_cuotas'] = cantidad_cuotas

        if not importe_total and monto_unitario:
            cuotas = cleaned_data.get('cantidad_cuotas', 1) or 1
            cleaned_data['importe_total'] = monto_unitario * cuotas

        return cleaned_data

    def clean_importe_total(self):
        importe = self.cleaned_data.get('importe_total')
        if importe and importe <= 0:
            raise forms.ValidationError('El importe debe ser mayor a 0.')
        return importe

    def clean_numero_cuota(self):
        numero_cuota = self.cleaned_data.get('numero_cuota')
        if not numero_cuota:
            return None
        partes = [p.strip() for p in str(numero_cuota).split(',') if p.strip()]
        if not partes:
            return None
        numeros = []
        for parte in partes:
            if not parte.isdigit():
                raise forms.ValidationError('Use solo números separados por comas.')
            if int(parte) <= 0:
                raise forms.ValidationError('Los números de cuota deben ser mayores a 0.')
            numeros.append(parte)
        return ','.join(numeros)


# ══════════════════════════════════════════════════════════════════════════
#  EGRESO FORM
# ══════════════════════════════════════════════════════════════════════════
class EgresoForm(forms.ModelForm):

    # ── Funcionario (solo visible para categoría SUELDOS) ────────────────
    funcionario = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Funcionario',
        empty_label='— Seleccionar funcionario —',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_funcionario',
        }),
        help_text='Seleccionar cuando el egreso corresponde a un sueldo.',
    )

    class Meta:
        model = Egreso
        fields = [
            'numero_comprobante', 'fecha', 'sede', 'categoria',
            'concepto', 'monto', 'comprobante', 'observaciones', 'funcionario',
        ]
        widgets = {
            'numero_comprobante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de factura o comprobante (opcional)',
            }),
            'fecha':       forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sede':        forms.Select(attrs={'class': 'form-select', 'required': True}),
            'categoria':   forms.Select(attrs={'class': 'form-select', 'id': 'id_categoria_egreso'}),
            'concepto':    forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción detallada del gasto'}),
            'monto':       forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'comprobante': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'numero_comprobante': 'Número de Comprobante',
            'fecha':    'Fecha del Gasto',
            'sede':     'Sede',
            'categoria':'Categoría',
            'concepto': 'Concepto',
            'monto':    'Monto (Gs.)',
            'comprobante': 'Comprobante/Factura',
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sede'].queryset           = Sede.objects.all().order_by('nombre')
        self.fields['funcionario'].queryset    = Funcionario.objects.filter(activo=True).order_by('apellido', 'nombre')
        self.fields['numero_comprobante'].required = False
        self.fields['observaciones'].required  = False
        self.fields['comprobante'].required    = False
        # Prellenar funcionario si existe
        if self.instance.pk and self.instance.funcionario:
            self.initial['funcionario'] = self.instance.funcionario

    def clean(self):
        cleaned_data = super().clean()
        categoria    = cleaned_data.get('categoria')
        funcionario  = cleaned_data.get('funcionario')
        # Si no es SUELDOS, limpiar el funcionario para no guardarlo
        if categoria != 'SUELDOS':
            cleaned_data['funcionario'] = None
        return cleaned_data


# ══════════════════════════════════════════════════════════════════════════
#  ASISTENCIA FORM
# ══════════════════════════════════════════════════════════════════════════
class AsistenciaForm(forms.ModelForm):

    # ── Horas trabajadas (opcional) ──────────────────────────────────────
    horas_trabajadas = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        label='Horas Trabajadas',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 8, 4.5',
            'step': '0.5',
            'min': '0',
            'max': '24',
            'id': 'id_horas_trabajadas',
        }),
        help_text='Opcional. Ingrese la cantidad de horas trabajadas ese día.',
    )

    class Meta:
        model = AsistenciaFuncionario
        fields = ['funcionario', 'fecha', 'presente', 'horas_trabajadas', 'observaciones']
        widgets = {
            'fecha':         forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'funcionario':   forms.Select(attrs={'class': 'form-select'}),
            'presente':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['funcionario'].queryset = Funcionario.objects.filter(activo=True)
        self.fields['observaciones'].required = False
        self.fields['horas_trabajadas'].required = False

    def clean_horas_trabajadas(self):
        horas = self.cleaned_data.get('horas_trabajadas')
        if horas is not None and horas > 24:
            raise forms.ValidationError('Las horas trabajadas no pueden superar 24 en un día.')
        return horas


# ══════════════════════════════════════════════════════════════════════════
#  ALUMNO FORM
# ══════════════════════════════════════════════════════════════════════════
class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = [
            'sede', 'carrera', 'nombre', 'apellido', 'cedula',
            'fecha_nacimiento', 'telefono', 'fecha_inicio', 'curso_actual',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
            'contacto_emergencia_relacion', 'activo',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_inicio':     forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre':   forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula':   forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'curso_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'contacto_emergencia_nombre':   forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_relacion': forms.TextInput(attrs={'class': 'form-control'}),
            'sede':    forms.Select(attrs={'class': 'form-select'}),
            'carrera': forms.Select(attrs={'class': 'form-select'}),
            'activo':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['cedula', 'fecha_nacimiento', 'telefono', 'fecha_inicio', 'curso_actual',
                  'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
                  'contacto_emergencia_relacion', 'activo']:
            self.fields[f].required = False


# ══════════════════════════════════════════════════════════════════════════
#  FUNCIONARIO FORM
# ══════════════════════════════════════════════════════════════════════════
class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['sede', 'nombre', 'apellido', 'cedula', 'cargo',
                  'telefono_principal', 'telefono_secundario', 'fecha_ingreso', 'activo']
        widgets = {
            'fecha_ingreso':       forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre':              forms.TextInput(attrs={'class': 'form-control'}),
            'apellido':            forms.TextInput(attrs={'class': 'form-control'}),
            'cedula':              forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_principal':  forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_secundario': forms.TextInput(attrs={'class': 'form-control'}),
            'sede':   forms.Select(attrs={'class': 'form-select'}),
            'cargo':  forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ══════════════════════════════════════════════════════════════════════════
#  SEDE FORM
# ══════════════════════════════════════════════════════════════════════════
class SedeForm(forms.ModelForm):
    class Meta:
        model = Sede
        fields = ['nombre', 'direccion', 'telefono', 'activa']
        widgets = {
            'nombre':    forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'telefono':  forms.TextInput(attrs={'class': 'form-control'}),
            'activa':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ══════════════════════════════════════════════════════════════════════════
#  CARRERA FORM
# ══════════════════════════════════════════════════════════════════════════
class CarreraForm(forms.ModelForm):
    class Meta:
        model = Carrera
        fields = ['nombre', 'naturalidad', 'duracion_meses', 'monto_matricula',
                  'monto_mensualidad', 'descripcion', 'activa']
        widgets = {
            'nombre':      forms.TextInput(attrs={'class': 'form-control'}),
            'naturalidad': forms.Select(attrs={'class': 'form-select'}),
            'duracion_meses':    forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'monto_matricula':   forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1000'}),
            'monto_mensualidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1000'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'activa':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ══════════════════════════════════════════════════════════════════════════
#  MATERIA FORM
# ══════════════════════════════════════════════════════════════════════════
class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nombre', 'bimestre', 'orden', 'fecha_examen_parcial', 'fecha_examen_final', 'link_classroom', 'docente']
        widgets = {
            'nombre':   forms.TextInput(attrs={'class': 'form-control'}),
            'bimestre': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '6'}),
            'orden':    forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'fecha_examen_parcial': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_examen_final':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'link_classroom': forms.URLInput(attrs={'class': 'form-control'}),
            'docente':  forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'fecha_examen_parcial': 'Examen Parcial',
            'fecha_examen_final':   'Examen Final',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['docente'].queryset   = Funcionario.objects.filter(cargo='DOCENCIA', activo=True)
        self.fields['docente'].empty_label = "Sin asignar"
        self.fields['fecha_examen_parcial'].required = False
        self.fields['fecha_examen_final'].required   = False