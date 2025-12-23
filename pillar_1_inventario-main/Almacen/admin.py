import json
from django import forms
from django.contrib import admin
from django.urls import reverse, path
from django.http import JsonResponse
from django.db import models
from Almacen.models.base.base import Unidad, Producto, Bloque
from Almacen.models.movimientos.movimientos import Inventario, Registro, PrestamoDevuelto, Transferencia
from Almacen.models.personal.personal import Empleado
from Almacen.models.requisiciones.requisiciones import Requisicion
from django.utils.html import format_html
from django.contrib import messages

class ProductoForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        label='Producto',
        required=True
    )
    cantidad = forms.DecimalField(
        label='Cantidad',
        min_value=0.01,
        required=True,
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )
    unidad = forms.ModelChoiceField(
        queryset=Unidad.objects.all(),
        label='Unidad',
        required=True
    )
    descripcion = forms.CharField(
        label='Descripción',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2})
    )

class RequisicionAdminForm(forms.ModelForm):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('supervisor', 'Aprobado por Supervisor'),
        ('autorizada', 'Autorizada'),
        ('rechazada', 'Rechazada'),
        ('surtida', 'Surtida'),
        ('cerrada', 'Cerrada')
    ]
    
    estado = forms.ChoiceField(choices=ESTADO_CHOICES)
    especialidad = forms.ChoiceField(
        label='Especialidad',
        choices=[],  # Se llenará en __init__
        required=True
    )
    detalles_productos = forms.JSONField(
        widget=forms.HiddenInput(),
        required=False,
        initial=list
    )
    
    class Meta:
        model = Requisicion
        fields = '__all__'
        widgets = {
            'detalles_productos': forms.HiddenInput()
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ocultar el campo ubicacion ya que usaremos bloque
        self.fields['ubicacion'].widget = forms.HiddenInput()
        
        # Configurar el campo especialidad con las opciones de Producto.ESPECIALIDAD_CHOICES
        especialidad_choices = [('', '---------')] + list(Producto.ESPECIALIDAD_CHOICES)
        self.fields['especialidad'].choices = especialidad_choices
        
        # Si ya existe la instancia (edición), hacer el campo de solo lectura
        if self.instance and self.instance.pk:
            # En lugar de deshabilitar, hacerlo de solo lectura
            self.fields['especialidad'].widget.attrs['readonly'] = 'readonly'
            self.fields['especialidad'].widget.attrs['class'] = 'readonly-specialidad'
            self.fields['especialidad'].help_text = 'Para cambiar la especialidad, cree una nueva requisición.'
            
            # Asegurar que el valor actual esté en las opciones
            current_value = self.instance.especialidad
            if current_value and not any(choice[0] == current_value for choice in self.fields['especialidad'].choices):
                self.fields['especialidad'].choices.append((current_value, current_value))
        
        # Inicializar detalles_productos si es nuevo
        if not self.instance.pk:
            self.instance.detalles_productos = []
            
        # Forzar que el widget sea un select
        self.fields['especialidad'].widget = forms.Select(choices=self.fields['especialidad'].choices)
            
    def clean_especialidad(self):
        # Si estamos editando, devolver el valor actual
        if self.instance and self.instance.pk:
            return self.instance.especialidad
            
        # Si es una nueva instancia, validar el valor
        especialidad = self.cleaned_data.get('especialidad')
        if not especialidad:
            raise forms.ValidationError('Debe seleccionar una especialidad')
        return especialidad
            
    def save(self, commit=True):
        # Actualizar automáticamente el campo ubicacion con el nombre del bloque seleccionado
        instance = super().save(commit=False)
        if instance.bloque:
            instance.ubicacion = instance.bloque.nombre
            
        # Obtener los detalles de los productos del formulario
        detalles_productos = self.data.get('detalles_productos')
        if detalles_productos:
            try:
                instance.detalles_productos = json.loads(detalles_productos)
            except (json.JSONDecodeError, TypeError):
                # Si hay un error al decodificar, mantener los detalles existentes
                pass
                
        if commit:
            instance.save()
        return instance

admin.site.site_header = 'Administrar almacén'
admin.site.index_title = 'Sitio administrativo'
admin.site.site_title = 'Dreacht & Struchtur'

admin.site.register(Unidad)

from django.contrib import admin
from django.utils.safestring import mark_safe

from django import forms
from Almacen.models.base.base import Producto

class ProductoAdminForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'especialidad': forms.Select(attrs={
                'id': 'id_especialidad',
                'class': 'vTextField',
                'onchange': 'handleEspecialidadChange(this.value)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mostrar todas las opciones de especialidad incluyendo 'herramienta'
        self.fields['especialidad'].choices = Producto.ESPECIALIDAD_CHOICES
    
    class Media:
        js = ('admin/js/producto_admin.js',)
    
    def clean(self):
        cleaned_data = super().clean()
        especialidad = cleaned_data.get('especialidad')
        
        # Si se selecciona 'herramienta' en el desplegable, marcar el booleano
        if especialidad == 'herramienta':
            cleaned_data['herramienta'] = True
        else:
            cleaned_data['herramienta'] = False
            
        return cleaned_data
    
    class Media:
        js = ('admin/js/producto_admin.js',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoAdminForm
    list_display = ('nombre', 'unidad', 'alerta', 'herramienta', 'get_especialidad_display')
    list_filter = ('herramienta', 'especialidad')
    exclude = ('herramienta',)  # Ocultar el campo booleano del formulario
    
    def get_especialidad_display(self, obj):
        return dict(Producto.ESPECIALIDAD_CHOICES).get(obj.especialidad, obj.especialidad)
    get_especialidad_display.short_description = 'Especialidad'

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('bloque', 'producto', 'get_unidad', 'es_herramienta_boolean', 'get_especialidad', 'cantidad')
    list_display_links = ('producto',)
    list_filter = ('bloque', 'producto__herramienta', 'producto__especialidad')
    readonly_fields = ('get_unidad', 'es_herramienta_boolean', 'get_especialidad')
    fieldsets = (
        (None, {
            'fields': ('bloque', 'producto', 'cantidad')
        }),
        ('Información del Producto', {
            'fields': ('get_unidad', 'es_herramienta_boolean', 'get_especialidad'),
            'classes': ('collapse',)
        }),
    )

    def get_unidad(self, obj):
        return obj.producto.unidad
    get_unidad.short_description = 'Unidad'
    
    def es_herramienta_boolean(self, obj):
        return bool(obj.producto.herramienta)
    es_herramienta_boolean.boolean = True
    es_herramienta_boolean.short_description = 'Es Herramienta'
    
    def get_especialidad(self, obj):
        return obj.producto.get_especialidad_display()
    get_especialidad.short_description = 'Especialidad'


admin.site.register(Bloque)

class RegistroForm(forms.ModelForm):
    class Meta:
        model = Registro
        exclude = ['cantidad', 'tipo', 'usuario']

@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ('bloque', 'empleado', 'fecha', 'producto', 'cantidad', 'tipo', 'usuario',)
    list_filter = ('bloque', 'empleado', 'fecha', 'producto', 'tipo', 'usuario',)
    form = RegistroForm

@admin.register(PrestamoDevuelto)
class PrestamoDevueltoAdmin(admin.ModelAdmin):
    list_display = ('bloque', 'empleado', 'producto', 'cantidad', 'fecha_entregado', 'entregado_por', 'fecha_recibido', 'recibido_por',)
    list_filter = ('bloque', 'empleado', 'producto', 'fecha_entregado', 'entregado_por', 'fecha_recibido', 'recibido_por',)

@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ('bloque_origen', 'bloque_destino', 'producto', 'cantidad','tipo', 'fecha_transferido', 'transferido_por', 'fecha_retornado', 'retornado_por',)

# -------------------------------modificado el 14/02/2025 see commits --------------------------------------------------------------------------
# ------------------------------- Requisiciones -------------------------------
@admin.register(Requisicion)
class RequisicionAdmin(admin.ModelAdmin):
    form = RequisicionAdminForm
    list_display = ('id', 'obra', 'estado_coloreado', 'fecha_soli', 'solicitante_info', 'supervisor_info', 'num_articulos', 'acciones')
    
    # Define los colores para cada estado
    ESTADO_COLORS = {
        'pendiente': '#ffc107',  # Amarillo
        'supervisor': '#17a2b8',  # Cian
        'autorizada': '#28a745',  # Verde
        'rechazada': '#dc3545',  # Rojo
        'surtida': '#6f42c1',    # Púrpura
        'cerrada': '#6c757d'     # Gris
    }
    list_filter = ('estado', 'especialidad', 'fecha_soli', 'bloque')
    search_fields = ('id', 'obra', 'ubicacion', 'solicitante_nombre', 'solicitante__nombre')
    readonly_fields = ('token_publico', 'usuario_creador', 'fecha_soli', 'detalles_productos_display', 'solicitante_display')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'get-productos-por-especialidad/<str:especialidad>/', 
                self.admin_site.admin_view(self.get_productos_por_especialidad),
                name='get_productos_por_especialidad',
            ),
        ]
        return custom_urls + urls
        
    def get_productos_por_especialidad(self, request, especialidad):
        """Vista para obtener productos filtrados por especialidad"""
        from django.db.models import Q
        
        if not especialidad or especialidad == 'None':
            return JsonResponse([], safe=False)
            
        # Obtener productos de la especialidad seleccionada MÁS los productos 'consumible'
        productos = Producto.objects.filter(
            Q(especialidad=especialidad) | Q(especialidad='consumible')
        ).values('id', 'nombre', 'unidad__nombre', 'especialidad')
        
        return JsonResponse(list(productos), safe=False)
    
    # Sobrescribir el template para incluir la interfaz de productos
    change_form_template = 'admin/Almacen/requisicion_change_form.html'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('estado', 'obra', 'ubicacion', 'bloque', 'especialidad')
        }),
        ('Solicitante', {
            'fields': ('solicitante', 'solicitante_nombre'),
            'description': 'Complete SOLO UNO de los dos campos de solicitante.'
        }),
        ('Detalles', {
            'fields': ('fecha_util', 'observaciones', 'imagen')
        }),
        ('Sistema', {
            'classes': ('collapse',),
            'fields': ('token_publico', 'usuario_creador', 'fecha_soli', 'detalles_productos_display')
        }),
    )
    
    def solicitante_display(self, obj):
        if obj.solicitante:
            return f"Empleado: {obj.solicitante}"
        elif obj.solicitante_nombre:
            return f"Invitado: {obj.solicitante_nombre}"
        return "No especificado"
    solicitante_display.short_description = 'Solicitante'
    
    def get_readonly_fields(self, request, obj=None):
        # Hacer que el campo de solicitante sea de solo lectura si ya existe un registro
        if obj:
            return self.readonly_fields + ('solicitante', 'solicitante_nombre')
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        # Guardar el usuario que realizó el cambio
        if not obj.usuario_creador:
            obj.usuario_creador = request.user
        
        # Obtener los detalles de los productos del formulario
        detalles_productos = form.data.get('detalles_productos')
        if detalles_productos:
            try:
                obj.detalles_productos = json.loads(detalles_productos)
            except json.JSONDecodeError:
                # Si hay un error al decodificar, mantener los detalles existentes
                pass
        
        # Si se cambió la especialidad, actualizar los productos
        if 'especialidad' in form.changed_data:
            # Aquí podrías agregar lógica adicional si es necesario
            pass
            
        # Guardar el objeto
        super().save_model(request, obj, form, change)
        
    def num_articulos(self, obj):
        """Muestra el número de artículos en la lista de requisiciones"""
        if hasattr(obj, 'detalles_productos') and obj.detalles_productos:
            return len(obj.detalles_productos)
        return 0
    num_articulos.short_description = 'Artículos'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['unidades'] = list(Unidad.objects.all())
        
        # Obtener la instancia actual
        obj = self.get_object(request, object_id)
        
        # Asegurarse de que detalles_productos sea una lista válida
        if obj:
            if not hasattr(obj, 'detalles_productos') or not isinstance(obj.detalles_productos, list):
                obj.detalles_productos = []
                obj.save(update_fields=['detalles_productos'])
            
            # Pasar los detalles de productos al contexto
            extra_context['detalles_productos'] = json.dumps(obj.detalles_productos) if obj.detalles_productos else '[]'
            extra_context['especialidad_actual'] = obj.especialidad if hasattr(obj, 'especialidad') else ''
        
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )
        
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Update the ubicacion choices to show Bloques
        form.base_fields['ubicacion'].widget.choices = [('', '---------')] + [
            (bloque.nombre, bloque.nombre) for bloque in Bloque.objects.all()
        ]
        
        # Asegurarse de que los detalles de productos se inicialicen correctamente
        if obj and (obj.detalles_productos is None or not isinstance(obj.detalles_productos, list)):
            obj.detalles_productos = []
            obj.save()
            
        return form
    
    def solicitante_info(self, obj):
        if obj.solicitante:
            return obj.solicitante.nombre
        return obj.solicitante_nombre or 'No especificado'
    solicitante_info.short_description = 'Solicitante'
    
    def supervisor_info(self, obj):
        if obj.supervisor:
            return obj.supervisor.nombre
        return 'No asignado'
    supervisor_info.short_description = 'Supervisor'
    
    def detalles_productos_display(self, obj):
        if not obj.detalles_productos:
            return 'Sin productos'
        
        detalles = []
        for i, detalle in enumerate(obj.obtener_productos(), 1):
            detalles.append(
                f"{i}. {detalle['producto'].nombre} - "
                f"{detalle['cantidad']} {detalle['unidad'].nombre}"
                f"{': ' + detalle['descripcion'] if detalle['descripcion'] else ''}"
            )
        return '\n'.join(detalles)
    detalles_productos_display.short_description = 'Productos Solicitados'
    
    def estado_coloreado(self, obj):
        # Mapeo de estados a sus etiquetas
        ESTADO_LABELS = {
            'pendiente': 'Pendiente',
            'supervisor': 'Aprobado por Supervisor',
            'autorizada': 'Autorizada',
            'rechazada': 'Rechazada',
            'surtida': 'Surtida',
            'cerrada': 'Cerrada'
        }
        
        color = self.ESTADO_COLORS.get(obj.estado, '#000000')
        estado_text = ESTADO_LABELS.get(obj.estado, obj.estado)
        
        return format_html(
            '<span style="background-color: {bg}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; display: inline-block; min-width: 120px; text-align: center;">{text}</span>',
            bg=color,
            text=estado_text
        )
    estado_coloreado.short_description = 'Estado'
    estado_coloreado.admin_order_field = 'estado'
    
    def acciones(self, obj):
        change_url = reverse('admin:Almacen_requisicion_change', args=[obj.id])
        
        if obj.estado == 'pendiente':
            return format_html(
                '<a class="button" href="{}" style="padding: 2px 8px; margin: 0 2px; background: #417690; color: white; text-decoration: none; border-radius: 4px;">Ver/Editar</a>',
                change_url
            )
        else:
            return format_html(
                '<a class="button" href="{}" style="padding: 2px 8px; margin: 0 2px; background: #447e9b; color: white; text-decoration: none; border-radius: 4px;">Ver</a>',
                change_url
            )
    acciones.short_description = 'Acciones'
    acciones.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        if not obj.usuario_creador_id:
            obj.usuario_creador = request.user
        super().save_model(request, obj, form, change)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'foto_thumbnail', 'puesto', 'rol', 'telefono', 'telefono_emergencia', 'acciones')
    list_filter = ('rol', 'puesto')
    search_fields = ('nombre', 'puesto', 'nss', 'tel', 'tel_emg')
    readonly_fields = ('foto_thumbnail', 'rol_help')
    
    def rol_help(self, obj):
        return "El rol predeterminado es 'Empleado'. Cámbielo solo si es necesario."
    rol_help.short_description = "Ayuda"
    rol_help.allow_tags = True
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Set default value for rol field
        form.base_fields['rol'].initial = 'empleado'
        return form
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', ('rol', 'puesto'), 'foto', 'foto_thumbnail')
        }),
        ('Información de Contacto', {
            'fields': ('direccion', 'tel', 'tel_emg'),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('nss', 'gafete_pdf', ('telegram_id', 'rol_help')),
            'classes': ('collapse',),
            'description': 'El campo de Telegram ID es opcional y se utiliza para notificaciones.'
        }),
    )

    def foto_thumbnail(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.foto.url)
        return "Sin foto"
    foto_thumbnail.short_description = 'Foto'
    foto_thumbnail.allow_tags = True

    def telefono(self, obj):
        return obj.tel or "-"
    telefono.short_description = 'Teléfono'

    def telefono_emergencia(self, obj):
        return obj.tel_emg or "-"
    telefono_emergencia.short_description = 'Tel. Emergencia'

    def acciones(self, obj):
        return format_html(
            '<a class="button" href="{}" target="_blank">Ver gafete</a>',
            reverse('ver_gafete', args=[obj.id]) if obj.gafete_pdf else '#'
        )
    acciones.short_description = 'Acciones'
    acciones.allow_tags = True

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:empleado_id>/ver_gafete/',
                self.admin_site.admin_view(self.ver_gafete),
                name='ver_gafete',
            ),
        ]
        return custom_urls + urls

    def ver_gafete(self, request, empleado_id):
        if empleado_id:
            url = reverse('gafete_pdf', args=[obj.id])
            return format_html('<a href="{}" target="_blank">Ver Gafete</a>', url)
        return "-"
    ver_gafete.short_description = "Gafete PDF"

    def response_add(self, request, obj, post_url_continue=None):
        pdf_url = reverse('gafete_pdf', args=[obj.id])
        messages.success(request, format_html('<a href="{}" target="_blank">📄 Haz clic aquí para ver el gafete</a>', pdf_url))
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        pdf_url = reverse('gafete_pdf', args=[obj.id])
        messages.success(request, format_html('<a href="{}" target="_blank">📄 Haz clic aquí para ver el gafete</a>', pdf_url))
        return super().response_change(request, obj)