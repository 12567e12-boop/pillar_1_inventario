from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from app_PDF_maker.forms import RequisicionForm, EmpleadoForm
from empleados.models import Empleado, Requisicion, DetalleRequisicion
from datetime import date, timedelta


class RequisicionFormTests(TestCase):
    """Tests para validar el formulario de requisiciones."""
    
    def test_valid_form(self):
        """Prueba que un formulario válido se valida correctamente."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        form_data = {
            'obra': 'Obra de prueba',
            'ubicacion': 'Ubicación test',
            'numero_de_articulos': 5,
            'fecha_soli': today,
            'fecha_util': tomorrow,
            'contratista_soli': 'Juan Pérez',
            'contratista_auto': '1',
            'especialidad': 'plomeria',
            'observaciones': 'Sin observaciones'
        }
        form = RequisicionForm(form_data)
        self.assertTrue(form.is_valid())
    
    def test_required_fields(self):
        """Prueba que los campos requeridos sean validados."""
        form_data = {
            'obra': '',  # Falta obra
            'ubicacion': 'Ubicación test',
        }
        form = RequisicionForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('obra', form.errors)
    
    def test_fecha_validation(self):
        """Prueba que las fechas sean validadas correctamente."""
        today = date.today()
        
        form_data = {
            'obra': 'Obra de prueba',
            'ubicacion': 'Ubicación test',
            'fecha_soli': today + timedelta(days=2),
            'fecha_util': today,  # La fecha_util es anterior a fecha_soli (inválido)
            'contratista_soli': 'Juan Pérez',
            'contratista_auto': '1',
            'especialidad': 'plomeria',
        }
        form = RequisicionForm(form_data)
        self.assertFalse(form.is_valid())
    
    def test_especialidad_required(self):
        """Prueba que especialidad es obligatorio."""
        today = date.today()
        
        form_data = {
            'obra': 'Obra de prueba',
            'ubicacion': 'Ubicación test',
            'fecha_soli': today,
            'contratista_soli': 'Juan Pérez',
            'contratista_auto': '1',
            # Falta especialidad
        }
        form = RequisicionForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('especialidad', form.errors)


class RequisicionModelTests(TestCase):
    """Tests para validar el modelo de Requisición."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.requisicion = Requisicion.objects.create(
            obra='Obra Test',
            ubicacion='Ubicación Test',
            fecha_soli=date.today(),
            solicitante_nombre='Test',
            supervisor_id_bigint=1
        )
    
    def test_requisicion_id_generation(self):
        """Prueba que el ID de requisición se genera correctamente."""
        self.assertIsNotNone(self.requisicion.id)
        # Formato esperado: OBRACONTRADATE (ej: OBRATESYYMMDD)
        self.assertTrue(len(self.requisicion.id) >= 11)
    
    def test_detalle_requisicion_auto_number(self):
        """Prueba que material_no se asigna automáticamente."""
        detalle1 = DetalleRequisicion.objects.create(
            requisicion=self.requisicion,
            descripcion='Material 1',
            unidad='kg',
            cantidad=10.5
        )
        detalle2 = DetalleRequisicion.objects.create(
            requisicion=self.requisicion,
            descripcion='Material 2',
            unidad='m',
            cantidad=5.0
        )
        
        # Verificar que se asignaron números secuenciales
        self.assertEqual(detalle1.material_no, 1)
        self.assertEqual(detalle2.material_no, 2)
    
    def test_numero_articulos_auto_update(self):
        """Prueba que numero_de_articulos se actualiza automáticamente."""
        DetalleRequisicion.objects.create(
            requisicion=self.requisicion,
            descripcion='Material 1',
            unidad='kg',
            cantidad=10
        )
        
        self.requisicion.actualizar_numero_de_articulos()
        self.assertEqual(self.requisicion.numero_de_articulos, 1)
