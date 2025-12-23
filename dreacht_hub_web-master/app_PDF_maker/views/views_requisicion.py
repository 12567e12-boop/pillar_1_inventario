import os
import logging
from io import BytesIO
from datetime import datetime, date
import pytz
import uuid
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.db import connection, connections

from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

from empleados.models import Requisicion, DetalleRequisicion
from app_PDF_maker.forms import RequisicionForm

logger = logging.getLogger(__name__)

# Función auxiliar para convertir string a date
def parse_fecha(fecha_str):
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def requisiciones(request):
    """Vista original para crear nuevas requisiciones."""
    tz = pytz.timezone("America/Mexico_City")
    fecha_hora_creacion = datetime.now(tz)

    if request.method == "POST":
        logger.info(f"POST data received: {dict(request.POST)}")
        
        form = RequisicionForm(request.POST)
        if form.is_valid():
            # Validate minimum items
            has_items = False
            for i in range(1, 15):
                desc = request.POST.get(f'item{i}_descripcion', '').strip()
                if desc:
                    has_items = True
                    break
            
            if not has_items:
                form.add_error(None, 'Debes agregar al menos un artículo para generar la requisición.')
                fecha_str = fecha_hora_creacion.strftime("%d/%m/%Y")
                hora_str = fecha_hora_creacion.strftime("%H:%M")
                return render(request, 'app_PDF_maker/requisiciones.html', {
                    'form': form,
                    "fecha_creacion": fecha_str,
                    "hora_creacion": hora_str
                })
            
            # Get validated data
            obra = form.cleaned_data['obra']
            ubicacion = form.cleaned_data['ubicacion']
            numero_de_articulos = form.cleaned_data.get('numero_de_articulos', 0)
            fecha_soli = form.cleaned_data['fecha_soli']
            fecha_util = form.cleaned_data['fecha_util']
            solicitante_nombre = form.cleaned_data['contratista_soli']
            supervisor_id_str = form.cleaned_data['contratista_auto']
            
            try:
                supervisor_id_bigint = int(supervisor_id_str) if supervisor_id_str else None
            except (ValueError, TypeError):
                logger.error(f"supervisor_id_bigint inválido: {supervisor_id_str}")
                supervisor_id_bigint = None
            
            especialidad = form.cleaned_data.get('especialidad', '')
            observaciones = form.cleaned_data.get('observaciones', '')
        else:
            # Form invalid - render with errors
            fecha_str = fecha_hora_creacion.strftime("%d/%m/%Y")
            hora_str = fecha_hora_creacion.strftime("%H:%M")
            return render(request, 'app_PDF_maker/requisiciones.html', {
                'form': form,
                "fecha_creacion": fecha_str,
                "hora_creacion": hora_str
            })

        try:
            # Prepare products JSON
            productos_list = []
            for i in range(1, 15):
                desc = request.POST.get(f'item{i}_descripcion', '').strip()
                unid = request.POST.get(f'item{i}_unidad', '').strip()
                cant = request.POST.get(f'item{i}_cantidad', '').strip()
                if desc:
                    productos_list.append({
                        'descripcion': desc,
                        'unidad_nombre': unid,
                        'cantidad': float(cant) if cant else 0,
                        'producto_id': None,
                        'unidad_id': None
                    })
            
            detalles_json = json.dumps(productos_list)
            
            # Generate UUID token and ID for new requisicion
            token_publico = str(uuid.uuid4())
            requisicion_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
            pdf_filename = f"requisiciones/{requisicion_id}.pdf"
            
            # INSERT new requisicion in Almacen_requisicion
            with connections['pilar'].cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Almacen_requisicion 
                    (id, obra, ubicacion, especialidad, solicitante_nombre, supervisor_id,
                     fecha_soli, fecha_util, observaciones, numero_de_articulos,
                     detalles_productos, imagen, token_publico, estado, 
                     autorizado_supervisor, autorizado_directivo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    requisicion_id, obra, ubicacion, especialidad,
                    solicitante_nombre, supervisor_id_bigint,
                    fecha_soli, fecha_util,
                    observaciones, int(numero_de_articulos) if numero_de_articulos else 0,
                    detalles_json, pdf_filename, token_publico, 'pendiente',
                    False, False
                ])
            
            logger.info(f"Nueva requisición creada: {requisicion_id}")
            
            # Also create in local database for tracking
            requisicion, creada = Requisicion.objects.get_or_create(
                obra=obra,
                ubicacion=ubicacion,
                solicitante_nombre=solicitante_nombre,
                supervisor_id_bigint=supervisor_id_bigint,
                defaults={
                    "numero_de_articulos": int(numero_de_articulos) if numero_de_articulos else 0,
                    "fecha_soli": fecha_soli,
                    "fecha_util": fecha_util,
                    "fecha_surt": None,
                    "especialidad": especialidad,
                    "observaciones": observaciones,
                }
            )
            
            if not requisicion.fecha_hora_creacion:
                requisicion.fecha_hora_creacion = fecha_hora_creacion
                requisicion.save(update_fields=["fecha_hora_creacion"])
            
            # Create details
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
            
            # Generate PDF (same code as before)
            base_pdf_path = os.path.join(settings.MEDIA_ROOT, 'requiscion_template.pdf')
            if not os.path.exists(base_pdf_path):
                logger.error(f"Plantilla PDF no encontrada en: {base_pdf_path}")
                return HttpResponse(f"Error: plantilla base no encontrada", status=500)
            
            try:
                base_reader = PdfReader(base_pdf_path)
                base_page = base_reader.pages[0]
                page_width = float(base_page.mediabox.width)
                page_height = float(base_page.mediabox.height)
            except Exception as e:
                logger.error(f"Error leyendo PDF base: {str(e)}")
                return HttpResponse(f"Error leyendo PDF base: {str(e)}", status=500)
            
            # Create overlay
            overlay_buffer = BytesIO()
            c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
            
            campos = {
                'obra':               (430, 1009, str(obra)),
                'ubicacion':          (470, 974, str(ubicacion)),
                'numero_de_articulos':(558, 936, str(numero_de_articulos or 0)),
                'fecha_soli':         (1250, 1009, fecha_soli.strftime("%Y-%m-%d") if fecha_soli else ""),
                'fecha_util':         (1250, 974, fecha_util.strftime("%Y-%m-%d") if fecha_util else ""),
                'fecha_surt':         (1250, 936, ""),
                'solicitante_nombre': (420, 885, str(solicitante_nombre)),
                'supervisor_id':      (275, 843, str(supervisor_id_bigint)),
                'especialidad':       (650, 797, str(especialidad)),
                'observaciones':      (50, 936, str(observaciones)),
                'fecha_creacion':     (1250, 875, fecha_str),
                'hora_creacion':      (1250, 850, hora_str),
            }
            
            # Add product details
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
            
            # Combine overlay with base PDF
            overlay_pdf = PdfReader(overlay_buffer)
            overlay_page = overlay_pdf.pages[0]
            
            writer = PdfWriter()
            base_page.merge_page(overlay_page)
            writer.add_page(base_page)
            
            final_buffer = BytesIO()
            writer.write(final_buffer)
            final_buffer.seek(0)
            
            # Save PDF to Inventario media folder
            try:
                inventory_media_req = settings.BASE_DIR.parent / 'pillar_1_inventario-main' / 'media' / 'requisiciones'
                os.makedirs(inventory_media_req, exist_ok=True)
                
                full_pdf_path = inventory_media_req / f"{requisicion_id}.pdf"
                
                with open(full_pdf_path, 'wb') as f:
                    f.write(final_buffer.getvalue())
                    
                logger.info(f"PDF guardado en: {full_pdf_path}")
                
            except Exception as e:
                logger.error(f"Error guardando archivo PDF: {e}")
            
            response = HttpResponse(final_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="requisicion_{requisicion_id}.pdf"'
            logger.info(f"PDF generado para nueva requisición: {requisicion_id}")
            return response
            
        except Exception as e:
            logger.exception(f"Error generando PDF: {str(e)}")
            return HttpResponse(f"Error generando PDF: {str(e)}", status=500)

    # --- GET request: precargar formulario ---
    form = RequisicionForm()
    fecha_str = fecha_hora_creacion.strftime("%d/%m/%Y")
    hora_str = fecha_hora_creacion.strftime("%H:%M")
    return render(request, 'app_PDF_maker/requisiciones.html', {
        'form': form,
        "fecha_creacion": fecha_str,
        "hora_creacion": hora_str
    })


def requisiciones_edit(request, token):
    """Load existing requisicion from Inventario by token for editing/completing."""
    tz = pytz.timezone("America/Mexico_City")
    fecha_hora_creacion = datetime.now(tz)
    
    # Remove hyphens from token to match database format (UUID stored without hyphens)
    token = token.replace('-', '')
    
    # Load requisicion from Inventario database
    try:
        with connections['pilar'].cursor() as cursor:
            cursor.execute("""
                SELECT id, obra, ubicacion, especialidad, solicitante_nombre, 
                       supervisor_id, fecha_soli, fecha_util, observaciones, 
                       detalles_productos, numero_de_articulos
                FROM Almacen_requisicion
                WHERE token_publico = %s
            """, [token])
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Requisición no encontrada con token: {token}")
                return HttpResponse("Requisición no encontrada", status=404)
            
            req_data = {
                'id': row[0],
                'obra': row[1],
                'ubicacion': row[2],
                'especialidad': row[3],
                'solicitante_nombre': row[4],
                'supervisor_id': row[5],
                'fecha_soli': str(row[6]) if row[6] else '',
                'fecha_util': str(row[7]) if row[7] else '',
                'observaciones': row[8] or '',
                'detalles_productos': row[9] or '[]',  # JSON string
                'numero_de_articulos': row[10] or 0,
            }
            
            logger.info(f"Requisición cargada: {req_data['id']} (token: {token})")
            
    except Exception as e:
        logger.error(f"Error loading requisicion by token {token}: {e}")
        return HttpResponse(f"Error cargando requisición: {e}", status=500)
    
    if request.method == "POST":
        # Handle form submission - UPDATE existing requisicion
        logger.info(f"POST data received for token {token}: {dict(request.POST)}")
        
        form = RequisicionForm(request.POST)
        if form.is_valid():
            # Validate minimum items
            has_items = False
            for i in range(1, 15):
                desc = request.POST.get(f'item{i}_descripcion', '').strip()
                if desc:
                    has_items = True
                    break
            
            if not has_items:
                form.add_error(None, 'Debes agregar al menos un artículo para generar la requisición.')
                fecha_str = fecha_hora_creacion.strftime("%d/%m/%Y")
                hora_str = fecha_hora_creacion.strftime("%H:%M")
                return render(request, 'app_PDF_maker/requisiciones.html', {
                    'form': form,
                    "fecha_creacion": fecha_str,
                    "hora_creacion": hora_str,
                    'req_data_json': json.dumps(req_data),
                    'token': token,
                    'edit_mode': True,
                })
            
            # Get validated data
            obra = form.cleaned_data['obra']
            ubicacion = form.cleaned_data['ubicacion']
            numero_de_articulos = form.cleaned_data.get('numero_de_articulos', 0)
            fecha_soli = form.cleaned_data['fecha_soli']
            fecha_util = form.cleaned_data['fecha_util']
            solicitante_nombre = form.cleaned_data['contratista_soli']
            supervisor_id_str = form.cleaned_data['contratista_auto']
            
            try:
                supervisor_id_bigint = int(supervisor_id_str) if supervisor_id_str else None
            except (ValueError, TypeError):
                logger.error(f"supervisor_id_bigint inválido: {supervisor_id_str}")
                supervisor_id_bigint = None
            
            especialidad = form.cleaned_data.get('especialidad', '')
            observaciones = form.cleaned_data.get('observaciones', '')
        else:
            # Form invalid - render with errors
            fecha_str = fecha_hora_creacion.strftime("%d/%m/%Y")
            hora_str = fecha_hora_creacion.strftime("%H:%M")
            return render(request, 'app_PDF_maker/requisiciones.html', {
                'form': form,
                "fecha_creacion": fecha_str,
                "hora_creacion": hora_str,
                'req_data_json': json.dumps(req_data),
                'token': token,
                'edit_mode': True,
            })

        try:
            # Prepare products JSON
            productos_list = []
            for i in range(1, 15):
                desc = request.POST.get(f'item{i}_descripcion', '').strip()
                unid = request.POST.get(f'item{i}_unidad', '').strip()
                cant = request.POST.get(f'item{i}_cantidad', '').strip()
                if desc:
                    productos_list.append({
                        'descripcion': desc,
                        'unidad_nombre': unid,
                        'cantidad': float(cant) if cant else 0,
                        'producto_id': None,
                        'unidad_id': None
                    })
            
            detalles_json = json.dumps(productos_list)
            
            # PDF filename
            requisicion_id = req_data['id']
            pdf_filename = f"requisiciones/{requisicion_id}.pdf"
            
            # UPDATE existing requisicion in Almacen_requisicion
            with connections['pilar'].cursor() as cursor:
                cursor.execute("""
                    UPDATE Almacen_requisicion 
                    SET obra = %s, ubicacion = %s, especialidad = %s,
                        solicitante_nombre = %s, supervisor_id = %s,
                        fecha_soli = %s, fecha_util = %s,
                        observaciones = %s, numero_de_articulos = %s,
                        detalles_productos = %s, imagen = %s
                    WHERE token_publico = %s
                """, [
                    obra, ubicacion, especialidad,
                    solicitante_nombre, supervisor_id_bigint,
                    fecha_soli, fecha_util,
                    observaciones, int(numero_de_articulos) if numero_de_articulos else 0,
                    detalles_json, pdf_filename, token
                ])
            
            logger.info(f"Requisición {requisicion_id} actualizada desde formulario web")
            
            # Also update/create in local database for tracking
            requisicion, creada = Requisicion.objects.get_or_create(
                obra=obra,
                ubicacion=ubicacion,
                solicitante_nombre=solicitante_nombre,
                supervisor_id_bigint=supervisor_id_bigint,
                defaults={
                    "numero_de_articulos": int(numero_de_articulos) if numero_de_articulos else 0,
                    "fecha_soli": fecha_soli,
                    "fecha_util": fecha_util,
                    "fecha_surt": None,
                    "especialidad": especialidad,
                    "observaciones": observaciones,
                }
            )
            
            if not requisicion.fecha_hora_creacion:
                requisicion.fecha_hora_creacion = fecha_hora_creacion
                requisicion.save(update_fields=["fecha_hora_creacion"])
            
            # Delete existing details and create new ones
            DetalleRequisicion.objects.filter(requisicion=requisicion).delete()
            
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
            
            # Get details for PDF
            detalles = DetalleRequisicion.objects.filter(requisicion=requisicion)
            
            fecha_str = requisicion.fecha_hora_creacion.strftime("%d/%m/%Y")
            hora_str = requisicion.fecha_hora_creacion.strftime("%H:%M")
            
            # Generate PDF
            base_pdf_path = os.path.join(settings.MEDIA_ROOT, 'requiscion_template.pdf')
            if not os.path.exists(base_pdf_path):
                logger.error(f"Plantilla PDF no encontrada en: {base_pdf_path}")
                return HttpResponse(f"Error: plantilla base no encontrada", status=500)
            
            try:
                base_reader = PdfReader(base_pdf_path)
                base_page = base_reader.pages[0]
                page_width = float(base_page.mediabox.width)
                page_height = float(base_page.mediabox.height)
            except Exception as e:
                logger.error(f"Error leyendo PDF base: {str(e)}")
                return HttpResponse(f"Error leyendo PDF base: {str(e)}", status=500)
            
            # Create overlay
            overlay_buffer = BytesIO()
            c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
            
            campos = {
                'obra':               (430, 1009, str(obra)),
                'ubicacion':          (470, 974, str(ubicacion)),
                'numero_de_articulos':(558, 936, str(numero_de_articulos or 0)),
                'fecha_soli':         (1250, 1009, fecha_soli.strftime("%Y-%m-%d") if fecha_soli else ""),
                'fecha_util':         (1250, 974, fecha_util.strftime("%Y-%m-%d") if fecha_util else ""),
                'fecha_surt':         (1250, 936, ""),
                'solicitante_nombre': (420, 885, str(solicitante_nombre)),
                'supervisor_id':      (275, 843, str(supervisor_id_bigint)),
                'especialidad':       (650, 797, str(especialidad)),
                'observaciones':      (50, 936, str(observaciones)),
                'fecha_creacion':     (1250, 875, fecha_str),
                'hora_creacion':      (1250, 850, hora_str),
            }
            
            # Add product details
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
            
            # Combine overlay with base PDF
            overlay_pdf = PdfReader(overlay_buffer)
            overlay_page = overlay_pdf.pages[0]
            
            writer = PdfWriter()
            base_page.merge_page(overlay_page)
            writer.add_page(base_page)
            
            final_buffer = BytesIO()
            writer.write(final_buffer)
            final_buffer.seek(0)
            
            # Save PDF to Inventario media folder
            try:
                inventory_media_req = settings.BASE_DIR.parent / 'pillar_1_inventario-main' / 'media' / 'requisiciones'
                os.makedirs(inventory_media_req, exist_ok=True)
                
                full_pdf_path = inventory_media_req / f"{requisicion_id}.pdf"
                
                with open(full_pdf_path, 'wb') as f:
                    f.write(final_buffer.getvalue())
                    
                logger.info(f"PDF guardado/actualizado en: {full_pdf_path}")
                
            except Exception as e:
                logger.error(f"Error guardando archivo PDF: {e}")
            
            response = HttpResponse(final_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="requisicion_{requisicion_id}.pdf"'
            logger.info(f"PDF generado/actualizado para requisición: {requisicion_id}")
            return response
            
        except Exception as e:
            logger.exception(f"Error generando PDF: {str(e)}")
            return HttpResponse(f"Error generando PDF: {str(e)}", status=500)
    
    # GET request: Pre-fill form with loaded data
    form = RequisicionForm(initial={
        'obra': req_data['obra'],
        'ubicacion': req_data['ubicacion'],
        'especialidad': req_data['especialidad'],
        'contratista_soli': req_data['solicitante_nombre'],
        'contratista_auto': str(req_data['supervisor_id']) if req_data['supervisor_id'] else '',
        'fecha_soli': req_data['fecha_soli'],
        'fecha_util': req_data['fecha_util'],
        'observaciones': req_data['observaciones'],
        'numero_de_articulos': req_data['numero_de_articulos'],
    })
    
    fecha_str = fecha_hora_creacion.strftime("%d/%m/%Y")
    hora_str = fecha_hora_creacion.strftime("%H:%M")
    
    return render(request, 'app_PDF_maker/requisiciones.html', {
        'form': form,
        'fecha_creacion': fecha_str,
        'hora_creacion': hora_str,
        'req_data_json': json.dumps(req_data),  # Pass as JSON string for JavaScript
        'token': token,
        'edit_mode': True,
    })
