import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from weasyprint import HTML
from django.template.loader import render_to_string
from .models.base.base import Empleado

#crear carpeta expediente de empleado --------------------------------------------------



#generar gafete ------------------------------------------------------------------------
@receiver(post_save, sender=Empleado)
def generar_gafete_automatico(sender, instance, created, **kwargs):
    if created:  # Solo cuando se crea un nuevo empleado
        html_string = render_to_string('gafete_pdf.html', {'empleado': instance})
        pdf = HTML(string=html_string).write_pdf()

        # Guardar el PDF en el modelo del empleado (opcional)
        instance.gafete_pdf.save(f'gafete_{instance.id}.pdf', ContentFile(pdf), save=False)



