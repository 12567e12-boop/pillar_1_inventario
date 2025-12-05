# Copia de app_PDF_maker/forms.py (solo RequisicionForm)
from django import forms
from django.core.exceptions import ValidationError

class RequisicionForm(forms.Form):
    obra = forms.CharField(max_length=200, required=True)
    ubicacion = forms.CharField(max_length=200, required=True)
    numero_de_articulos = forms.IntegerField(required=False, min_value=0)
    fecha_soli = forms.DateField(required=True)
    fecha_util = forms.DateField(required=False)
    fecha_surt = forms.DateField(required=False)
    contratista_soli = forms.CharField(max_length=200, required=True)
    contratista_auto = forms.CharField(max_length=200, required=True)
    area_util = forms.CharField(max_length=200, required=True)
    observaciones = forms.CharField(required=False, widget=forms.Textarea)
    def clean(self):
        cleaned_data = super().clean()
        fecha_soli = cleaned_data.get('fecha_soli')
        fecha_util = cleaned_data.get('fecha_util')
        fecha_surt = cleaned_data.get('fecha_surt')
        if fecha_soli and fecha_util and fecha_soli > fecha_util:
            raise ValidationError('La fecha de solicitud no puede ser posterior a la fecha de utilidad.')
        if fecha_util and fecha_surt and fecha_util > fecha_surt:
            raise ValidationError('La fecha de utilidad no puede ser posterior a la fecha de surtimiento.')
        return cleaned_data
