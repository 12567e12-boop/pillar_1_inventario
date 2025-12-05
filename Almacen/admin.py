from django import forms
from django.contrib import admin
from django.urls import reverse
from Almacen.models.base.base import Unidad, Producto, Bloque
from Almacen.models.movimientos.movimientos import Inventario, Registro, PrestamoDevuelto, Transferencia
from Almacen.models.personal.personal import Empleado
from django.utils.html import format_html
from django.contrib import messages

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