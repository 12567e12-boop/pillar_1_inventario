import os
from io import BytesIO

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

from ..forms import EmpleadoForm

# ===================================
# Páginas simples
# ===================================
def home(request):
    return render(request, 'app_PDF_maker/home.html')

def recursos(request):
    return render(request, 'app_PDF_maker/recursos.html')

# ===================================
# Generación de gafetes
# ===================================
def gafetes(request):
    if request.method == "POST":
        form = EmpleadoForm(request.POST, request.FILES)
        if form.is_valid():
            area = form.cleaned_data.get('area')

            # Elegir plantillas según área
            if area == 'cyber_robotics':
                frente_path = os.path.join(settings.BASE_DIR, 'app_PDF_maker', 'static', 'media', 'cyber_front_gafete.jpg')
                reverso_path = os.path.join(settings.BASE_DIR, 'app_PDF_maker', 'static', 'media', 'cyber_back_gafete.jpg')
                empresa = "Cyber"
            elif area == 'dreacht_strukchur':
                frente_path = os.path.join(settings.BASE_DIR, 'app_PDF_maker', 'static', 'media', 'dreacht_front_gafete.jpg')
                reverso_path = os.path.join(settings.BASE_DIR, 'app_PDF_maker', 'static', 'media', 'dreacht_back_gafete.jpg')
                empresa = "Dreacht"
            else:
                frente_path = os.path.join(settings.BASE_DIR, 'app_PDF_maker', 'static', 'media', 'dreacht_front_gafete.jpg')
                reverso_path = os.path.join(settings.BASE_DIR, 'app_PDF_maker', 'static', 'media', 'dreacht_back_gafete.jpg')
                empresa = "Dreacht"

            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # ======= LADO FRONTAL =======
            frente = ImageReader(frente_path)
            c.drawImage(frente, 0, 0, width=width, height=height)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(120, 500, form.cleaned_data['nombre'])
            c.setFont("Helvetica", 12)
            c.drawString(120, 480, form.cleaned_data['puesto'])

            # Foto del empleado
            if form.cleaned_data.get('foto'):
                uploaded_file = form.cleaned_data['foto']
                image_bytes = uploaded_file.read()
                image_io = BytesIO(image_bytes)
                foto = ImageReader(image_io)
                c.drawImage(foto, 50, 400, width=100, height=100)

            c.showPage()

            # ======= LADO TRASERO =======
            reverso = ImageReader(reverso_path)
            c.drawImage(reverso, 0, 0, width=width, height=height)
            c.setFont("Helvetica", 10)
            c.drawString(100, 200, f"Tel: {form.cleaned_data.get('tel', '')}")
            c.drawString(100, 180, f"Emergencia: {form.cleaned_data.get('tel_emg', '')}")
            c.drawString(100, 160, f"NSS: {form.cleaned_data.get('nss', '')}")

            c.save()
            buffer.seek(0)

            empleado = form.save()
            nombre_pdf = f'gafete de {empleado.nombre} {empresa}.pdf'
            empleado.gafete_pdf.save(nombre_pdf, buffer)
            empleado.save()

            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{nombre_pdf}"'
            return response
    else:
        form = EmpleadoForm()

    return render(request, 'app_PDF_maker/gafetes.html', {'form': form})
