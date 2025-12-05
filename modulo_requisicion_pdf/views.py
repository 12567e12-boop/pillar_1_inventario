# Copia de app_PDF_maker/views/views_requisicion.py
import os
from io import BytesIO
from datetime import datetime
import pytz
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from .models import Requisicion, DetalleRequisicion
from .forms import RequisicionForm

def requisiciones(request):
    tz = pytz.timezone("America/Mexico_City")
    fecha_hora_creacion = datetime.now(tz)
    if request.method == "POST":
        form = RequisicionForm(request.POST)
        if form.is_valid():
            obra = form.cleaned_data['obra']
            ubicacion = form.cleaned_data['ubicacion']
            numero_de_articulos = form.cleaned_data.get('numero_de_articulos', 0)
            fecha_soli = form.cleaned_data['fecha_soli']
            fecha_util = form.cleaned_data['fecha_util']
            fecha_surt = form.cleaned_data['fecha_surt']
            contratista_soli = form.cleaned_data['contratista_soli']
            contratista_auto = form.cleaned_data['contratista_auto']
            area_util = form.cleaned_data['area_util']
            observaciones = form.cleaned_data.get('observaciones', '')
        else:
            fecha_str = fecha_hora_creacion.strftime("%d/%m/%Y")
            hora_str = fecha_hora_creacion.strftime("%H:%M")
            return render(request, 'modulo_requisicion_pdf/requisiciones.html', {
                'form': form,
                "fecha_creacion": fecha_str,
                "hora_creacion": hora_str
            })
        try:
            requisicion, creada = Requisicion.objects.get_or_create(
                obra=obra,
                ubicacion=ubicacion,
                contratista_soli=contratista_soli,
                contratista_auto=contratista_auto,
                defaults={
                    "numero_de_articulos": int(numero_de_articulos) if numero_de_articulos else 0,
                    "fecha_soli": fecha_soli,
                    "fecha_util": fecha_util,
                    "fecha_surt": fecha_surt,
                    "area_util": area_util,
                    "observaciones": observaciones,
                }
            )
            if not requisicion.fecha_hora_creacion:
                requisicion.fecha_hora_creacion = fecha_hora_creacion
                requisicion.save(update_fields=["fecha_hora_creacion"])
            for i in range(1, 15):
                descripcion = request.POST.get(f'item{i}_descripcion', '').strip()
                unidad = request.POST.get(f'item{i}_unidad', '').strip()
                cantidad_str = request.POST.get(f'item{i}_cantidad', '').strip()
                if descripcion:
                    try:
                        cantidad = float(cantidad_str) if cantidad_str else 0.0
                        DetalleRequisicion.objects.create(
                            requisicion=requisicion,
                            descripcion=descripcion,
                            unidad=unidad,
                            cantidad=cantidad
                        )
                    except ValueError:
                        pass
            detalles = DetalleRequisicion.objects.filter(requisicion=requisicion)
            fecha_str = requisicion.fecha_hora_creacion.strftime("%d/%m/%Y")
            hora_str = requisicion.fecha_hora_creacion.strftime("%H:%M")
            base_pdf_path = os.path.join(settings.BASE_DIR, 'modulo_requisicion_pdf', 'static', 'media', 'requiscion_template.pdf')
            if not os.path.exists(base_pdf_path):
                return HttpResponse(f"Error: plantilla base no encontrada en {base_pdf_path}", status=500)
            base_reader = PdfReader(base_pdf_path)
            base_page = base_reader.pages[0]
            page_width = float(base_page.mediabox.width)
            page_height = float(base_page.mediabox.height)
            overlay_buffer = BytesIO()
            c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
            campos = {
                'obra':               (430, 1009, str(obra)),
                'ubicacion':          (470, 974, str(ubicacion)),
                'numero_de_articulos':(558, 936, str(numero_de_articulos or 0)),
                'fecha_soli':         (1250, 1009, fecha_soli.strftime("%Y-%m-%d") if fecha_soli else ""),
                'fecha_util':         (1250, 974, fecha_util.strftime("%Y-%m-%d") if fecha_util else ""),
                'fecha_surt':         (1250, 936, fecha_surt.strftime("%Y-%m-%d") if fecha_surt else ""),
                'contratista_soli':   (420, 885, str(contratista_soli)),
                'contratista_auto':   (275, 843, str(contratista_auto)),
                'area_util':          (400, 797, str(area_util)),
                'observaciones':      (50, 936, str(observaciones)),
                'fecha_creacion':     (1250, 875, fecha_str),
                'hora_creacion':      (1250, 850, hora_str),
            }
            y_start = 450
            for i, detalle in enumerate(detalles, start=1):
                y_pos = page_height - y_start - (i - 1) * 20
                campos[f'item{i}_descripcion'] = (50, y_pos, detalle.descripcion)
                campos[f'item{i}_unidad'] = (200, y_pos, detalle.unidad)
                campos[f'item{i}_cantidad'] = (250, y_pos, str(detalle.cantidad))
            c.setFont("Helvetica", 18)
            for x, y, text in campos.values():
                if text:
                    c.drawString(x, y, str(text))
            c.showPage()
            c.save()
            overlay_buffer.seek(0)
            overlay_pdf = PdfReader(overlay_buffer)
            overlay_page = overlay_pdf.pages[0]
            writer = PdfWriter()
            base_page.merge_page(overlay_page)
            writer.add_page(base_page)
            final_buffer = BytesIO()
            writer.write(final_buffer)
            final_buffer.seek(0)
            response = HttpResponse(final_buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="requisicion_completada.pdf"'
            return response
        except Exception as e:
            return HttpResponse(f"Error generando PDF: {str(e)}", status=500)
    form = RequisicionForm()
    fecha_str = fecha_hora_creacion.strftime("%d/%m/%Y")
    hora_str = fecha_hora_creacion.strftime("%H:%M")
    return render(request, 'modulo_requisicion_pdf/requisiciones.html', {
        'form': form,
        "fecha_creacion": fecha_str,
        "hora_creacion": hora_str
    })
