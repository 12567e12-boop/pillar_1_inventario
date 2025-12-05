import datetime
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from Almacen.models.base.base import Unidad, Producto, Bloque
from Almacen.models.movimientos.movimientos import Inventario, Registro, PrestamoDevuelto, Transferencia
from Almacen.models.personal.personal import Empleado

@login_required
def index(request):
    return render(request, "base.html", {})



def error403(request):
    return render(request, "error403.html", {})

def error404(request):
    return render(request, "error404.html", {})

def dashboard(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/pages/error403')
    return render(request, "dashboard.html", {
        'existencias': Inventario.objects.all(),
        'bloques': Bloque.objects.all(),
        'empleados': Empleado.objects.all(),
        'productos': Producto.objects.all(),
        'unidades': Unidad.objects.all(),
        'registros': Registro.objects.all().order_by('-pk')[:5],
    })

def registros(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/pages/error403')
    return render(request, "registros.html", {
        'bloques': Bloque.objects.all(),
        'unidades': Unidad.objects.all(),
        'registros': Registro.objects.all(),
        'usuarios': User.objects.all()
    })

def transferencias(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/pages/error403')
    return render(request, "transferencias.html", {
        'bloques': Bloque.objects.all(),
        'unidades': Unidad.objects.all(),
        'transferencias': Transferencia.objects.filter(tipo=1),
        'usuarios': User.objects.all()
    })

def prestados(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/pages/error403')
    return render(request, "prestados.html", {
        'registros': Registro.objects.filter(tipo=-1),
        'devueltos': PrestamoDevuelto.objects.all(),
        'bloques': Bloque.objects.all(),
        'unidades': Unidad.objects.all(),
        'usuarios': User.objects.all()
    })

def temporales(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/pages/error403')
    return render(request, "temporales.html", {
        'temporales': Transferencia.objects.filter(tipo=0),
        'retornados': Transferencia.objects.filter(tipo=-1),
        'bloques': Bloque.objects.all(),
        'unidades': Unidad.objects.all(),
        'usuarios': User.objects.all()
    })

def registro_add(request):
    if not request.user.is_authenticated:
        return HttpResponse('Acceso prohibido, recargue la página y vuelva a intentarlo.')
    if not request.user.has_perm('Almacen.can_use_register_form'):
        return HttpResponse('Acceso prohibido, no tiene permisos para utilizar este formulario.')
    if request.method == 'POST':
        try:
            bloque = limpiarEspaciosDobles(request.POST['bloque'])
            empleado = limpiarEspaciosDobles(request.POST['empleado'])
            producto = limpiarEspaciosDobles(request.POST['producto'])
            unidad = limpiarEspaciosDobles(request.POST['unidad'])
            cantidad = request.POST['cantidad']
            tipo = int(request.POST['tipo'])
        except:
            return HttpResponse('Faltan datos por llenar en el formulario.')
        try:
            alerta = request.POST['alerta']
            if alerta != '':
                alerta = float(alerta)
                if alerta < 0:
                    alerta = 0
        except:
            alerta = 0
        if bloque == '' or empleado == '' or producto == '' or cantidad == '':
            return HttpResponse('Faltan datos por llenar en el formulario.')
        try:
            cantidad = float(cantidad)
        except ValueError:
            return HttpResponse('La cantidad debe ser un NUMERO.')
        if tipo != 0 and tipo != 1 and tipo != -1:
            return HttpResponse('El tipo debe ser ENTRADA, SALIDA o PRESTADO.')
        try:
            o_bloque = Bloque.objects.get(nombre=bloque)
        except Bloque.DoesNotExist:
            o_bloque = Bloque(nombre=bloque)
            o_bloque.save()
        try:
            o_empleado = Empleado.objects.get(nombre=empleado)
        except Empleado.DoesNotExist:
            o_empleado = Empleado(nombre=empleado)
            o_empleado.save()
        try:
            o_producto = Producto.objects.get(nombre=producto)
        except Producto.DoesNotExist:
            if (unidad == ''):
                return HttpResponse('Para los productos nuevos se debe especificar la unidad de medida obligatoriamente.')
            try:
                o_unidad = Unidad.objects.get(nombre=unidad)
            except Unidad.DoesNotExist:
                o_unidad = Unidad(nombre=unidad)
                o_unidad.save()
            o_producto = Producto(nombre=producto, unidad=o_unidad)
            o_producto.save()
        if tipo == 1 and alerta != '':
            o_producto.alerta = alerta
            o_producto.save()
        if cantidad <= 0:
            return HttpResponse('La cantidad debe ser mayor que CERO.')
        try:
            o_inventario = Inventario.objects.get(bloque=o_bloque, producto=o_producto)
        except Inventario.DoesNotExist:
            if tipo != 1:
                return HttpResponse('Ese producto no tiene existencias en el ALMACEN en este momento.')
            o_inventario = Inventario(bloque=o_bloque, producto=o_producto)
            o_inventario.save()
        if tipo != 1 and o_inventario.cantidad < cantidad:
            return HttpResponse('La cantidad de existencias (' + str(o_inventario.cantidad) + ') no es suficiente para despachar la cantidad solicitada (' + str(cantidad) + ').')
        o_registro = Registro(bloque=o_bloque, empleado=o_empleado, producto=o_producto, cantidad=cantidad, tipo=tipo, usuario=request.user)
        o_registro.save()
        alerta = False
        if tipo == 1:
            o_inventario.cantidad += cantidad
        else:
            if o_inventario.cantidad - cantidad <= o_producto.alerta:
                alerta = 'Registro guardado correctamente. La cantidad restante (' + str(o_inventario.cantidad - cantidad) + ') es menor o igual a la alerta configurada (' + str(o_producto.alerta) + ').'
            o_inventario.cantidad -= cantidad
        if o_inventario.cantidad == 0:
            o_inventario.delete()
        else:
            o_inventario.save()
        if alerta:
            return HttpResponse(alerta)
        return HttpResponse('OK')
    return HttpResponse('Los datos se deben enviar mediante POST, contacte al desarrollador.')

def registro_devolver(request):
    if not request.user.is_authenticated:
        return HttpResponse('Acceso prohibido, recargue la página y vuelva a intentarlo.')
    if not request.user.has_perm('Almacen.add_prestamodevuelto'):
        return HttpResponse('Acceso prohibido, no tiene permisos para devolver productos.')
    if request.method == 'POST':
        try:
            id = request.POST['id']
        except:
            return HttpResponse('No se pudo obtener el ID, recargue la página y vuelva a intentarlo.')
        try:
            o_registro = Registro.objects.get(pk=id)
        except Bloque.DoesNotExist:
            return HttpResponse('El registro del prestamo ya no existe en la base de datos.')
        o_devuelto = PrestamoDevuelto(bloque=o_registro.bloque, empleado=o_registro.empleado, producto=o_registro.producto, cantidad=o_registro.cantidad)
        o_devuelto.fecha_entregado = o_registro.fecha
        o_devuelto.entregado_por = o_registro.usuario
        o_devuelto.recibido_por = request.user
        o_devuelto.save()
        try:
            o_inventario = Inventario.objects.get(bloque=o_registro.bloque, producto=o_registro.producto)
        except Inventario.DoesNotExist:
            o_inventario = Inventario(bloque=o_registro.bloque, producto=o_registro.producto)
            o_inventario.save()
        o_inventario.cantidad += o_registro.cantidad
        o_inventario.save()
        o_registro.delete()
        return HttpResponse('OK')
    return HttpResponse('Los datos se deben enviar mediante POST, contacte al desarrollador.')

def registro_refresh(request):
    if not request.user.is_authenticated:
        return HttpResponse('NO')
    if not request.user.has_perm('Almacen.view_registro'):
        return HttpResponse('NO')
    if request.method == 'POST':
        registros = Registro.objects.all().order_by('-pk')[:5]
        if registros:
            result = ''
            for p in registros:
                result += '<tr><td style="white-space:nowrap">' + str(p.pk) + '</td><td style="white-space:nowrap">'
                result += p.bloque.__str__() + '</td><td style="white-space:nowrap">' + p.empleado.__str__() + '</td><td style="white-space:nowrap">'
                result += str(p.fecha) + '</td><td style="white-space:nowrap">' + p.producto.__str__() + '</td><td style="white-space:nowrap">'
                result += p.producto.unidad.__str__() + '</td><td style="white-space:nowrap">' + str(p.cantidad) + '</td><td style="white-space:nowrap">'
                if p.tipo == 1:
                    result += 'Entrada'
                elif p.tipo == 0:
                    result += 'Salida'
                else:
                    result += 'Prestado'
                result += '</td><td style="white-space:nowrap">' + p.usuario.username.upper() + '</td></tr>'                                    
            return HttpResponse(result)
        else:
            return HttpResponse('<tr><td colspan="9" style="color: orange;">No hay elementos que mostrar. La tabla se encuentra vac&iacute;a en este momento.</td></tr>')
    return HttpResponse('NO')

def transferencia_retornar(request):
    if not request.user.is_authenticated:
        return HttpResponse('Acceso prohibido, recargue la página y vuelva a intentarlo.')
    if not request.user.has_perm('Almacen.edit_transferencia'):
        return HttpResponse('Acceso prohibido, no tiene permisos para retornar transferencias.')
    if request.method == 'POST':
        try:
            id = request.POST['id']
        except:
            return HttpResponse('No se pudo obtener el ID, recargue la página y vuelva a intentarlo.')
        try:
            o_transferencia = Transferencia.objects.get(pk=id)
        except Bloque.DoesNotExist:
            return HttpResponse('El registro de la transferencia ya no existe en la base de datos.')
        try:
            o_inventario_origen = Inventario.objects.get(bloque=o_transferencia.bloque_destino, producto=o_transferencia.producto)
        except Inventario.DoesNotExist:
            return HttpResponse('Ese producto no tiene existencias en el ALMACEN para ese bloque en este momento.')
        if o_inventario_origen.cantidad < o_transferencia.cantidad:
            return HttpResponse('La cantidad de existencias (' + str(o_inventario_origen.cantidad) + ') no es suficiente para retornar la cantidad solicitada (' + str(o_transferencia.cantidad) + ').')
        try:
            o_inventario_destino = Inventario.objects.get(bloque=o_transferencia.bloque_origen, producto=o_transferencia.producto)
        except Inventario.DoesNotExist:
            o_inventario_destino = Inventario(bloque=o_transferencia.bloque_origen, producto=o_transferencia.producto)
            o_inventario_destino.save()
        o_inventario_destino.cantidad += o_transferencia.cantidad
        o_inventario_origen.cantidad -= o_transferencia.cantidad
        if o_inventario_origen.cantidad == 0:
            o_inventario_origen.delete()
        else:
            o_inventario_origen.save()
        o_inventario_destino.save()
        o_transferencia.tipo = -1
        o_transferencia.fecha_retornado = datetime.datetime.now()
        o_transferencia.retornado_por = request.user
        o_transferencia.save()
        return HttpResponse('OK')
    return HttpResponse('Los datos se deben enviar mediante POST, contacte al desarrollador.')

def bloque_exists(request):
    if not request.user.is_authenticated:
        return HttpResponse('AUTH')
    if request.method == 'POST':
        try:
            bloque = request.POST['bloque']
        except:
            return HttpResponse('DATA')
        try:
            Bloque.objects.get(nombre=bloque)
            return HttpResponse('YES')
        except Bloque.DoesNotExist:
            return HttpResponse('NO')
    return HttpResponse('METHOD')

def empleado_exists(request):
    if not request.user.is_authenticated:
        return HttpResponse('AUTH')
    if request.method == 'POST':
        try:
            empleado = request.POST['empleado']
        except:
            return HttpResponse('DATA')
        try:
            Empleado.objects.get(nombre=empleado)
            return HttpResponse('YES')
        except Empleado.DoesNotExist:
            return HttpResponse('NO')
    return HttpResponse('METHOD')

def producto_transferir(request):
    if not request.user.is_authenticated:
        return HttpResponse('Acceso prohibido, recargue la página y vuelva a intentarlo.')
    if not request.user.has_perm('Almacen.can_use_register_form'):
        return HttpResponse('Acceso prohibido, no tiene permisos para utilizar este formulario.')
    if request.method == 'POST':
        try:
            bloque_origen = limpiarEspaciosDobles(request.POST['bloque_origen'])
            bloque_destino = limpiarEspaciosDobles(request.POST['bloque_destino'])
            producto_transferir = limpiarEspaciosDobles(request.POST['producto_transferir'])
            cantidad_transferir = request.POST['cantidad_transferir']
            tipo_transferencia = int(request.POST['tipo_transferencia'])
        except:
            return HttpResponse('Faltan datos por llenar en el formulario.')
        if bloque_origen == '' or bloque_destino == '' or producto_transferir == '' or cantidad_transferir == '':
            return HttpResponse('Faltan datos por llenar en el formulario.')
        if bloque_origen == bloque_destino:
            return HttpResponse('El bloque de ORIGEN y el de DESTINO no pueden ser iguales.')
        try:
            cantidad_transferir = float(cantidad_transferir)
        except ValueError:
            return HttpResponse('La cantidad debe ser un NUMERO.')
        if tipo_transferencia != 0 and tipo_transferencia != 1:
            return HttpResponse('El tipo debe ser PERMANENTE o TEMPORAL.')
        try:
            o_bloque_origen = Bloque.objects.get(nombre=bloque_origen)
        except Bloque.DoesNotExist:
            return HttpResponse('El bloque de origen no existe en la base de datos.')
        try:
            o_bloque_destino = Bloque.objects.get(nombre=bloque_destino)
        except Bloque.DoesNotExist:
            return HttpResponse('El bloque de destino no existe en la base de datos.')
        try:
            o_producto_transferir = Producto.objects.get(nombre=producto_transferir)
        except Producto.DoesNotExist:
            return HttpResponse('El producto a transferir no existe en la base de datos.')
        if cantidad_transferir <= 0:
            return HttpResponse('La cantidad a transferir debe ser mayor que CERO.')
        try:
            o_inventario_origen = Inventario.objects.get(bloque=o_bloque_origen, producto=o_producto_transferir)
        except Inventario.DoesNotExist:
            return HttpResponse('Ese producto no tiene existencias en el ALMACEN para ese bloque en este momento.')
        if o_inventario_origen.cantidad < cantidad_transferir:
            return HttpResponse('La cantidad de existencias (' + str(o_inventario_origen.cantidad) + ') no es suficiente para transferir la cantidad solicitada (' + str(cantidad_transferir) + ').')
        try:
            o_inventario_destino = Inventario.objects.get(bloque=o_bloque_destino, producto=o_producto_transferir)
        except Inventario.DoesNotExist:
            o_inventario_destino = Inventario(bloque=o_bloque_destino, producto=o_producto_transferir)
            o_inventario_destino.save()
        o_transferencia = Transferencia(bloque_origen=o_bloque_origen, bloque_destino=o_bloque_destino, producto=o_producto_transferir, cantidad=cantidad_transferir)
        o_transferencia.tipo = tipo_transferencia
        o_transferencia.transferido_por = request.user
        o_transferencia.save()
        o_inventario_destino.cantidad += cantidad_transferir
        o_inventario_origen.cantidad -= cantidad_transferir
        if o_inventario_origen.cantidad == 0:
            o_inventario_origen.delete()
        else:
            o_inventario_origen.save()
        o_inventario_destino.save()
        return HttpResponse('OK')
    return HttpResponse('Los datos se deben enviar mediante POST, contacte al desarrollador.')

def producto_exists(request):
    if not request.user.is_authenticated:
        return HttpResponse('AUTH')
    if request.method == 'POST':
        try:
            producto = request.POST['producto']
        except:
            return HttpResponse('DATA')
        try:
            Producto.objects.get(nombre=producto)
            return HttpResponse('YES')
        except Producto.DoesNotExist:
            return HttpResponse('NO')
    return HttpResponse('METHOD')

def unidad_exists(request):
    if not request.user.is_authenticated:
        return HttpResponse('AUTH')
    if request.method == 'POST':
        try:
            unidad = request.POST['unidad']
        except:
            return HttpResponse('DATA')
        try:
            Unidad.objects.get(nombre=unidad)
            return HttpResponse('YES')
        except Unidad.DoesNotExist:
            return HttpResponse('NO')
    return HttpResponse('METHOD')

def inventario_refresh(request):
    if not request.user.is_authenticated:
        return HttpResponse('NO')
    if not request.user.has_perm('Almacen.view_inventario'):
        return HttpResponse('NO')
    if request.method == 'POST':
        existencias = Inventario.objects.all()
        if existencias:
            result = ''
            for p in existencias:
                result += '<tr><td>' + str(p.producto.pk) + '</td><td style="white-space:nowrap">' + p.bloque.__str__() + '</td><td style="white-space:nowrap">' + p.producto.__str__() + '</td><td>'
                result += p.producto.unidad.__str__() + '</td><td>'
                result += str(p.cantidad) + '</td></tr>'
            return HttpResponse(result)
    return HttpResponse('NO')

def devueltos_refresh(request):
    if not request.user.is_authenticated:
        return HttpResponse('NO')
    if not request.user.has_perm('Almacen.view_prestamodevuelto'):
        return HttpResponse('NO')
    if request.method == 'POST':
        devueltos = PrestamoDevuelto.objects.all()
        if devueltos:
            result = ''
            for p in devueltos:
                result += '<tr><td style="white-space:nowrap">' + str(p.pk) + '</td><td style="white-space:nowrap">'
                result += p.bloque.__str__() + '</td><td style="white-space:nowrap">' + p.empleado.__str__() + '</td><td style="white-space:nowrap">'
                result += p.producto.__str__() + '</td><td style="white-space:nowrap">' + p.producto.unidad.__str__() + '</td><td style="white-space:nowrap">'
                result += str(p.cantidad) + '</td><td style="white-space:nowrap">' + str(p.fecha_entregado) + '</td><td style="white-space:nowrap">'
                result += p.entregado_por.username.upper() + '</td><td style="white-space:nowrap">' + str(p.fecha_recibido) + '</td><td style="white-space:nowrap">'
                result += p.recibido_por.username.upper() + '</td></tr>'
            return HttpResponse(result)
    return HttpResponse('NO')

def retornados_refresh(request):
    if not request.user.is_authenticated:
        return HttpResponse('NO')
    if not request.user.has_perm('Almacen.view_transferencia'):
        return HttpResponse('NO')
    if request.method == 'POST':
        retornados = Transferencia.objects.filter(tipo=-1)
        if retornados:
            result = ''
            for p in retornados:
                result += '<tr><td style="white-space:nowrap">' + str(p.pk) + '</td><td style="white-space:nowrap">'
                result += p.bloque_origen.__str__() + '</td><td style="white-space:nowrap">' + p.bloque_destino.__str__() + '</td>'
                result += '<td style="white-space:nowrap">' + p.producto.__str__() + '</td><td style="white-space:nowrap">'
                result += p.producto.unidad.__str__() + '</td><td style="white-space:nowrap">' + str(p.cantidad) + '</td>'
                result += '<td style="white-space:nowrap">' + str(p.fecha_transferido) + '</td><td style="white-space:nowrap">'
                result += p.transferido_por.username.upper() + '</td><td style="white-space:nowrap">' + str(p.fecha_retornado)
                result += '</td><td style="white-space:nowrap">' + p.retornado_por.username.upper() + '</td></tr>'
            return HttpResponse(result)
    return HttpResponse('NO')

# FUNCIONES AUXILIARES COMUNES
def limpiarEspaciosDobles(text):
    result = text.replace('  ', ' ')
    while (len(result) < len(text)):
        text = result
        result = text.replace('  ', ' ')
    return result


#------------------------------- 14/02/2025 --------------------------------------
# ============== Nuevo: Generar PDF ==============
from django.template.loader import render_to_string
from weasyprint import HTML

def generar_gafete_pdf(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)

    # Renderizar plantilla con MEDIA_URL disponible
    html_string = render_to_string('gafete_pdf.html', {
        'empleado': empleado,
        'MEDIA_URL': settings.MEDIA_URL  # Pasar MEDIA_URL a la plantilla
    })

    # Generar PDF
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    # Responder con el PDF generado
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="gafete_{empleado.nombre}.pdf"'
    return response