from django import forms
from .models import Pago, Alumno, Funcionario, AsistenciaFuncionario, Sede, Carrera, Materia
from django.contrib.auth.models import User

class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Contraseña'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Confirmar Contraseña'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es un usuario nuevo, la contraseña es requerida
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        # Solo validar contraseñas si se están creando o cambiando
        if password or password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Las contraseñas no coinciden.')

            if len(password) < 8:
                raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')

        return cleaned_data


class PagoForm(forms.ModelForm):
    # Campo adicional para cliente diferenciado
    es_cliente_diferenciado = forms.BooleanField(
        required=False,
        label='Cliente Diferenciado',
        help_text='Marcar si el pago no es de un alumno regular',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'onchange': 'toggleClienteDiferenciado()'
        })
    )

    # Campos para cliente diferenciado
    nombre_cliente = forms.CharField(
        required=False,
        max_length=200,
        label='Nombre del Cliente',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del cliente'
        })
    )

    validez_pago = forms.DateField(
        required=False,
        label='Validez del Pago',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    fecha_vencimiento = forms.DateField(
        required=False,
        label='Fecha de Vencimiento',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    curso = forms.CharField(
        required=False,
        max_length=200,
        label='Curso',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del curso'
        })
    )

    monto_unitario = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=0,
        label='Monto Unitario (Gs.)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '1',
            'placeholder': 'Monto por cuota'
        })
    )

    cantidad_cuotas = forms.IntegerField(
        required=False,
        label='Cantidad de Cuotas',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'value': '1',
            'placeholder': 'Número de cuotas a pagar'
        })
    )

    class Meta:
        model = Pago
        fields = [
            'numero_recibo',
            'fecha',
            'alumno',
            'sede',
            'numero_cuota',
            'concepto',
            'importe_total',
            'foto_comprobante',
            'observaciones'
        ]
        widgets = {
            'numero_recibo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Se generará automáticamente',
                'readonly': 'readonly'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'alumno': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'sede': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'numero_cuota': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Ej: 1, 2, 3...'
            }),
            'concepto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del pago'
            }),
            'importe_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': 'Monto en Guaraníes',
                'readonly': 'readonly'
            }),
            'foto_comprobante': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones adicionales (opcional)'
            })
        }
        labels = {
            'numero_recibo': 'Número de Recibo',
            'fecha': 'Fecha de Pago',
            'alumno': 'Alumno',
            'sede': 'Sede',
            'numero_cuota': 'Número de Cuota',
            'concepto': 'Concepto',
            'importe_total': 'Importe Total (Gs.)',
            'foto_comprobante': 'Foto del Comprobante',
            'observaciones': 'Observaciones'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ordenar alumnos alfabéticamente
        self.fields['alumno'].queryset = Alumno.objects.all().order_by('apellido', 'nombre')

        # Ordenar sedes alfabéticamente
        self.fields['sede'].queryset = Sede.objects.all().order_by('nombre')

        # Hacer el número de recibo opcional (se generará automáticamente)
        self.fields['numero_recibo'].required = False

        # Hacer las observaciones y foto opcionales
        self.fields['observaciones'].required = False
        self.fields['foto_comprobante'].required = False

        # Si estamos editando y hay datos previos de cliente diferenciado
        if self.instance.pk and hasattr(self.instance, 'nombre_cliente'):
            if self.instance.nombre_cliente:
                self.initial['es_cliente_diferenciado'] = True
                self.initial['nombre_cliente'] = self.instance.nombre_cliente
                if hasattr(self.instance, 'validez_pago'):
                    self.initial['validez_pago'] = self.instance.validez_pago
                if hasattr(self.instance, 'fecha_vencimiento'):
                    self.initial['fecha_vencimiento'] = self.instance.fecha_vencimiento
                if hasattr(self.instance, 'curso'):
                    self.initial['curso'] = self.instance.curso
                if hasattr(self.instance, 'monto_unitario'):
                    self.initial['monto_unitario'] = self.instance.monto_unitario
                if hasattr(self.instance, 'cantidad_cuotas'):
                    self.initial['cantidad_cuotas'] = self.instance.cantidad_cuotas

    def clean(self):
        cleaned_data = super().clean()
        es_cliente_diferenciado = cleaned_data.get('es_cliente_diferenciado')
        alumno = cleaned_data.get('alumno')
        nombre_cliente = cleaned_data.get('nombre_cliente')
        cantidad_cuotas = cleaned_data.get('cantidad_cuotas', 1)
        monto_unitario = cleaned_data.get('monto_unitario', 0)

        # Validar que si no es alumno regular, tenga nombre de cliente
        if es_cliente_diferenciado:
            if not nombre_cliente:
                raise forms.ValidationError('Debe ingresar el nombre del cliente')
            # Hacer alumno no obligatorio
            cleaned_data['alumno'] = None
        else:
            if not alumno:
                raise forms.ValidationError('Debe seleccionar un alumno')

        # Calcular importe total si hay monto unitario y cantidad de cuotas
        if monto_unitario and cantidad_cuotas:
            cleaned_data['importe_total'] = monto_unitario * cantidad_cuotas

        return cleaned_data

    def clean_importe_total(self):
        importe = self.cleaned_data.get('importe_total')
        if importe and importe <= 0:
            raise forms.ValidationError('El importe debe ser mayor a 0')
        return importe

    def clean_numero_cuota(self):
        numero_cuota = self.cleaned_data.get('numero_cuota')
        if numero_cuota and numero_cuota <= 0:
            raise forms.ValidationError('El número de cuota debe ser mayor a 0')
        return numero_cuota

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = [
            'sede', 'carrera', 'nombre', 'apellido', 'cedula',
            'fecha_nacimiento', 'telefono', 'fecha_inicio', 'curso_actual',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
            'contacto_emergencia_relacion', 'activo'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'curso_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'contacto_emergencia_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_relacion': forms.TextInput(attrs={'class': 'form-control'}),
            'sede': forms.Select(attrs={'class': 'form-select'}),
            'carrera': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            'sede', 'nombre', 'apellido', 'cedula', 'cargo',
            'telefono_principal', 'telefono_secundario',
            'fecha_ingreso', 'activo'
        ]
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_secundario': forms.TextInput(attrs={'class': 'form-control'}),
            'sede': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = AsistenciaFuncionario
        fields = ['funcionario', 'fecha', 'presente', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'presente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo funcionarios activos
        self.fields['funcionario'].queryset = Funcionario.objects.filter(activo=True)


class SedeForm(forms.ModelForm):
    class Meta:
        model = Sede
        fields = ['nombre', 'direccion', 'telefono', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CarreraForm(forms.ModelForm):
    class Meta:
        model = Carrera
        fields = ['nombre', 'naturalidad', 'duracion_meses', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'naturalidad': forms.Select(attrs={'class': 'form-select'}),
            'duracion_meses': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nombre', 'bimestre', 'orden', 'link_classroom', 'docente']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'bimestre': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '6'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'link_classroom': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'https://classroom.google.com/...'}),
            'docente': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar docentes activos
        self.fields['docente'].queryset = Funcionario.objects.filter(cargo='DOCENCIA', activo=True)
        self.fields['docente'].empty_label = "Sin asignar"