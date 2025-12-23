from django import forms
from django.core.exceptions import ValidationError
from django.db import connection, connections
from datetime import date
import logging

from empleados.models import Empleado, Requisicion

logger = logging.getLogger(__name__)


class EmpleadoForm(forms.ModelForm):
    GAFETE_CHOICES = [
        ('cyber_robotics', 'Cyber robotics'),
        ('dreacht_strukchur', 'Dreacht & Strukchur'),
    ]

    area = forms.ChoiceField(
        choices=GAFETE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Área"
    )

    class Meta:
        model = Empleado
        exclude = ['gafete_pdf', 'fecha_alta', 'fecha_baja', 'nomina']
        error_messages = {
            'nombre': {
                'required': 'Este campo es obligatorio.',
            },
            'foto': {
                'required': 'Este campo es obligatorio.',
            },
            'puesto': {
                'required': 'Este campo es obligatorio.',
            },
            'area': {
                'required': 'Este campo es obligatorio.',
            },
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'puesto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contratista'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección (Opcional)'
            }),
            'nss': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NSS (Opcional)'
            }),
            'tel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono (Opcional)'
            }),
            'tel_emg': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de Emergencia (Opcional)'
            }),
        }


class RequisicionForm(forms.Form):
    obra = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'campo',
            'id': 'campo-obra',
            'placeholder': 'Ej. traumatologia'
        }),
        error_messages={
            'required': 'El campo obra es obligatorio.',
            'max_length': 'La obra no puede exceder 200 caracteres.'
        }
    )
    ubicacion = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={
            'class': 'campo',
            'id': 'campo-ubicacion'
        }),
        error_messages={
            'required': 'El campo ubicación es obligatorio.'
        }
    )
    numero_de_articulos = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'campo',
            'id': 'campo-numero_de_articulos',
            'placeholder': 'numero de articulos'
        }),
        error_messages={
            'min_value': 'El número de artículos debe ser positivo.',
            'invalid': 'El número de artículos debe ser un entero.'
        }
    )
    fecha_soli = forms.DateField(
        required=True,
        initial=date.today,
        widget=forms.DateInput(attrs={
            'class': 'campo',
            'id': 'campo-fecha_soli',
            'type': 'date',
            'readonly': 'readonly'
        }),
        error_messages={
            'required': 'La fecha de solicitud es obligatoria.',
            'invalid': 'Formato de fecha inválido.'
        }
    )
    fecha_util = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'campo',
            'id': 'campo-fecha_util',
            'type': 'date'
        }),
        error_messages={
            'invalid': 'Formato de fecha inválido.'
        }
    )
    contratista_soli = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'campo',
            'id': 'campo-contratista_soli',
            'placeholder': 'Nombre completo'
        }),
        error_messages={
            'required': 'El solicitante es obligatorio.',
            'max_length': 'El nombre no puede exceder 200 caracteres.'
        }
    )
    contratista_auto = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={
            'class': 'campo',
            'id': 'campo-contratista_auto',
            'name': 'contratista_auto'
        }),
        error_messages={
            'required': 'El supervisor es obligatorio.'
        }
    )
    ESPECIALIDAD_CHOICES = [
        ('', '--- Selecciona una especialidad ---'),
        ('plomeria', 'Plomería'),
        ('electricidad', 'Electricidad'),
        ('obra civil', 'Obra Civil'),
        ('vidrio y canceleria', 'Vidrio y Cancelería'),
        ('pintura y tablaroca', 'Pintura y Tablaroca'),
        ('herreria', 'Herrería'),
        ('herramienta', 'Herramienta'),
        ('limpieza', 'Limpieza'),
    ]
    
    especialidad = forms.ChoiceField(
        choices=ESPECIALIDAD_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'campo',
            'id': 'campo-especialidad'
        }),
        error_messages={
            'required': 'La especialidad es obligatoria.'
        }
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'campo',
            'id': 'campo-observaciones',
            'placeholder': 'Observaciones',
            'rows': '4',
            'cols': '50'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_soli = cleaned_data.get('fecha_soli')
        fecha_util = cleaned_data.get('fecha_util')
        
        # Convertir contratista_auto a entero si es string
        contratista_auto = cleaned_data.get('contratista_auto')
        if contratista_auto:
            try:
                # Si es string, convertir a int
                if isinstance(contratista_auto, str):
                    cleaned_data['contratista_auto'] = int(contratista_auto)
            except (ValueError, TypeError) as e:
                logger.error(f"Error convirtiendo contratista_auto a int: {contratista_auto}, error: {e}")
                raise ValidationError(f"supervisor_id debe ser un número, recibido: {contratista_auto}")

        if fecha_soli and fecha_util:
            if fecha_soli > fecha_util:
                raise ValidationError('La fecha de solicitud no puede ser posterior a la fecha de utilidad.')
            
            # Validar máximo 2 semanas (14 días)
            from datetime import timedelta
            if fecha_util > fecha_soli + timedelta(days=14):
                raise ValidationError('La fecha de utilidad no puede ser mayor a 2 semanas después de la solicitud.')

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate ubicacion choices from almacen_bloque.nombre table (using pilar DB)
        try:
            with connections['pilar'].cursor() as cursor:
                cursor.execute("SELECT nombre FROM Almacen_bloque ORDER BY nombre")
                rows = [r[0] for r in cursor.fetchall()]
            choices = [('', '--- Selecciona una ubicación ---')] + [(r, r) for r in rows]
        except Exception as e:
            logger.exception("Error cargando ubicaciones desde Almacen_bloque (pilar): %s", e)
            choices = [('', '--- Selecciona una ubicación ---')]

        # If form was submitted with a ubicacion value not in DB, include it so validation doesn't fail
        submitted = None
        try:
            # self.data works for bound forms
            submitted = (self.data.get('ubicacion') if hasattr(self, 'data') else None)
        except Exception:
            submitted = None

        if submitted and submitted not in [c[0] for c in choices]:
            choices.append((submitted, submitted))

        self.fields['ubicacion'].choices = choices

        # Populate contratista_auto choices from almacen_empleado where rol='supervisor'
        # Format: (id, nombre) so we store the ID in the DB
        try:
            with connections['pilar'].cursor() as cursor:
                cursor.execute("SELECT id, nombre FROM Almacen_empleado WHERE rol = 'supervisor' ORDER BY nombre")
                rows = cursor.fetchall()
            ca_choices = [('', '--- Selecciona quien autoriza ---')] + [(str(r[0]), r[1]) for r in rows]
            logger.info(f"Supervisor choices: {ca_choices}")  # Debug
        except Exception as e:
            logger.exception("Error cargando supervisores desde almacen_empleado: %s", e)
            ca_choices = [('', '--- Selecciona quien autoriza ---')]

        # include submitted value if present
        submitted_ca = None
        try:
            submitted_ca = (self.data.get('contratista_auto') if hasattr(self, 'data') else None)
        except Exception:
            submitted_ca = None

        if submitted_ca and submitted_ca not in [c[0] for c in ca_choices]:
            # Si el ID enviado no está en BD, agregarlo temporalmente
            ca_choices.append((submitted_ca, f"ID: {submitted_ca}"))

        self.fields['contratista_auto'].choices = ca_choices
