from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone

from Almacen.models.requisiciones.requisiciones import Requisicion
from Almacen.models.base.base import Producto, Unidad, Bloque
from Almacen.models.personal.personal import Empleado

@login_required
def lista_requisiciones(request):
    """
    Muestra todas las requisiciones del usuario actual
    """
    requisiciones = Requisicion.objects.filter(usuario_creador=request.user).order_by('-fecha_soli')
    return render(request, 'requisiciones/lista.html', {
        'requisiciones': requisiciones
    })

@login_required
def detalle_requisicion(request, token_publico):
    """
    Muestra el detalle de una requisición específica
    """
    requisicion = get_object_or_404(Requisicion, token_publico=token_publico)
    
    # Verificar que el usuario tenga permiso para ver esta requisición
    if not request.user.is_staff and requisicion.usuario_creador != request.user:
        return HttpResponseForbidden("No tiene permiso para ver esta requisición")
    
    return render(request, 'requisiciones/detalle.html', {
        'requisicion': requisicion,
        'productos': requisicion.obtener_productos()
    })

@login_required
def crear_requisicion(request):
    """
    Crea una nueva requisición
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear la requisición
                requisicion = Requisicion(
                    obra=request.POST.get('obra', ''),
                    ubicacion=request.POST.get('ubicacion', ''),
                    especialidad=request.POST.get('especialidad', 'General'),
                    solicitante_nombre=request.POST.get('solicitante_nombre', ''),
                    usuario_creador=request.user,
                    observaciones=request.POST.get('observaciones', '')
                )
                
                # Asignar bloque si se especificó
                bloque_id = request.POST.get('bloque')
                if bloque_id:
                    requisicion.bloque = Bloque.objects.get(id=bloque_id)
                
                # Asignar solicitante si se especificó
                solicitante_id = request.POST.get('solicitante')
                if solicitante_id:
                    requisicion.solicitante = Empleado.objects.get(id=solicitante_id)
                
                # Generar ID y guardar
                requisicion.generar_id()
                requisicion.save()
                
                # Agregar productos si los hay
                productos = request.POST.getlist('productos[]')
                cantidades = request.POST.getlist('cantidades[]')
                unidades = request.POST.getlist('unidades[]')
                descripciones = request.POST.getlist('descripciones[]', [])
                
                for i, producto_id in enumerate(productos):
                    if i >= 14:  # No permitir más de 14 productos
                        break
                    if producto_id and cantidades[i]:
                        try:
                            requisicion.agregar_producto(
                                producto_id=producto_id,
                                cantidad=cantidades[i],
                                unidad_id=unidades[i],
                                descripcion=descripciones[i] if i < len(descripciones) else ''
                            )
                        except (Producto.DoesNotExist, Unidad.DoesNotExist, ValueError) as e:
                            messages.error(request, f"Error al agregar producto: {str(e)}")
                
                messages.success(request, 'Requisición creada exitosamente')
                return redirect('detalle_requisicion', token_publico=requisicion.token_publico)
                
        except Exception as e:
            messages.error(request, f'Error al crear la requisición: {str(e)}')
    
    # Si es GET o hubo un error, mostrar el formulario
    bloques = Bloque.objects.all()
    empleados = Empleado.objects.all()
    productos = Producto.objects.all()
    unidades = Unidad.objects.all()
    
    return render(request, 'requisiciones/crear.html', {
        'bloques': bloques,
        'empleados': empleados,
        'productos': productos,
        'unidades': unidades,
        'especialidades': dict(Producto.ESPECIALIDAD_CHOICES)
    })

@login_required
def aprobar_requisicion_supervisor(request, token_publico):
    """
    Vista para que el supervisor apruebe una requisición
    """
    if not request.user.has_perm('Almacen.aprobar_requisicion'):
        return HttpResponseForbidden("No tiene permiso para aprobar requisiciones")
    
    requisicion = get_object_or_404(Requisicion, token_publico=token_publico)
    
    try:
        # Obtener el empleado supervisor actual
        supervisor = Empleado.objects.get(usuario=request.user)
        requisicion.aprobar_supervisor(supervisor=supervisor, usuario=request.user)
        messages.success(request, 'Requisición aprobada por el supervisor')
    except Exception as e:
        messages.error(request, f'Error al aprobar la requisición: {str(e)}')
    
    return redirect('detalle_requisicion', token_publico=token_publico)

@login_required
def aprobar_requisicion_directivo(request, token_publico):
    """
    Vista para que el directivo apruebe una requisición
    """
    if not request.user.has_perm('Almacen.aprobar_requisicion_directivo'):
        return HttpResponseForbidden("No tiene permiso para aprobar requisiciones a nivel directivo")
    
    requisicion = get_object_or_404(Requisicion, token_publico=token_publico)
    
    try:
        requisicion.aprobar_directivo(usuario=request.user)
        messages.success(request, 'Requisición aprobada por el directivo')
    except Exception as e:
        messages.error(request, f'Error al aprobar la requisición: {str(e)}')
    
    return redirect('detalle_requisicion', token_publico=token_publico)

@login_required
def rechazar_requisicion(request, token_publico):
    """
    Vista para rechazar una requisición
    """
    if not request.user.has_perm('Almacen.aprobar_requisicion'):
        return HttpResponseForbidden("No tiene permiso para rechazar requisiciones")
    
    requisicion = get_object_or_404(Requisicion, token_publico=token_publico)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', 'Sin motivo especificado')
        try:
            requisicion.estado = 'rechazada'
            requisicion.observaciones = f"{requisicion.observaciones or ''}\n---\nRechazada por: {request.user.get_full_name() or request.user.username}\nMotivo: {motivo}"
            requisicion.save()
            messages.success(request, 'Requisición rechazada exitosamente')
        except Exception as e:
            messages.error(request, f'Error al rechazar la requisición: {str(e)}')
    
    return redirect('detalle_requisicion', token_publico=token_publico)

@login_required
def api_productos_por_especialidad(request):
    """
    API para obtener productos por especialidad
    """
    especialidad = request.GET.get('especialidad')
    if not especialidad:
        return JsonResponse({'error': 'Especialidad no especificada'}, status=400)
    
    productos = Producto.objects.filter(especialidad=especialidad).values('id', 'nombre', 'unidad__nombre')
    return JsonResponse(list(productos), safe=False)
