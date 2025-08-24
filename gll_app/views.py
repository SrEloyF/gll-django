from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib import messages
from django.http import HttpResponse
import os
from django.conf import settings
import pymysql
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.urls import reverse
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

def filtros(request):
    columna = request.GET.get('columna', '')
    valor = request.GET.get('valor', '')
    page = request.GET.get('page', 1)

    queryset = Gallo.objects.all()

    # Diccionario para mapear columna a filtro
    filtros_map = {
        'nroPlaca': 'nroPlaca__nroPlaca__icontains',
        'fechaNac': 'fechaNac__icontains',
        'color': 'color__nombre__icontains',
        'sexo': 'sexo__icontains',
        'tipoGallo': 'tipoGallo__icontains',
        'peso': 'peso__peso__icontains',
        'nroPlacaAnterior': 'nroPlacaAnterior__nroPlaca__icontains',
        'nombreDuenoAnterior': 'nombreDuenoAnterior__nombre__icontains',
        'estadoDeSalud': 'estadoDeSalud__nombre__icontains',
        'fechaMuerte': 'fechaMuerte__icontains',
    }

    if columna and valor and columna in filtros_map:
        filtro = {filtros_map[columna]: valor}
        queryset = queryset.filter(**filtro)

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(page)

    return render(request, 'filtros.html', {
        'page_obj': page_obj,
        'columna': columna,
        'valor': valor,
    })

@csrf_exempt
def peso_create_ajax(request):
    if request.method == 'POST':
        peso = request.POST.get('peso', '').strip()
        try:
            peso_val = float(peso)
        except ValueError:
            return JsonResponse({'error': 'Peso inválido.'}, status=400)
        if not peso or peso_val <= 0:
            return JsonResponse({'error': 'El peso es requerido y debe ser positivo.'}, status=400)
        if PesosCheck.objects.filter(peso=peso_val).exists():
            return JsonResponse({'error': 'Ya existe ese peso.'}, status=400)
        nuevo_peso = PesosCheck.objects.create(peso=peso_val)
        return JsonResponse({'success': True, 'id': nuevo_peso.id, 'peso': str(nuevo_peso.peso)})
    return JsonResponse({'error': 'Método no permitido.'}, status=405)


@csrf_exempt
def placa_create_ajax(request):
    if request.method == 'POST':
        nroPlaca = request.POST.get('nroPlaca', '').strip()
        if not nroPlaca:
            return JsonResponse({'error': 'El número de placa es requerido.'}, status=400)
        if PlacaCheck.objects.filter(nroPlaca=nroPlaca).exists():
            return JsonResponse({'error': 'Ya existe una placa con ese número.'}, status=400)
        placa = PlacaCheck.objects.create(nroPlaca=nroPlaca)
        return JsonResponse({'success': True, 'id': placa.nroPlaca, 'nroPlaca': placa.nroPlaca})
    return JsonResponse({'error': 'Método no permitido.'}, status=405)

paginas = 10

def export_db(request):
    db_settings = settings.DATABASES['default']
    connection = pymysql.connect(
        host=db_settings['HOST'],
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        db=db_settings['NAME']
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            output_file = os.path.join(settings.BASE_DIR, 'exported_db.sql')

            with open(output_file, 'w') as f:
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SHOW CREATE TABLE {table_name}")
                    create_table_statement = cursor.fetchone()[1]
                    f.write(f"{create_table_statement};\n\n")
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()

                    for row in rows:
                        values = ', '.join([str(value) for value in row])
                        f.write(f"INSERT INTO {table_name} VALUES ({values});\n")

            print(f"Base de datos exportada exitosamente a {output_file}")
        with open(output_file, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/sql')
            response['Content-Disposition'] = 'attachment; filename=exported_db.sql'
            return response
    
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

    finally:
        connection.close()

def index(request):
    sexo_inicial = 'todos'
    page_inicial = request.GET.get('page', 1)
    error_eliminacion = request.GET.get('error_eliminacion') == '1'

    if sexo_inicial == 'todos':
        queryset = Gallo.objects.all().order_by('nroPlaca')
    else:
        queryset = Gallo.objects.filter(sexo=sexo_inicial).order_by('nroPlaca')

    paginator = Paginator(queryset, paginas)
    page_obj = paginator.get_page(page_inicial)

    cantidad_machos = Gallo.objects.filter(sexo='M').count()
    cantidad_hembras = Gallo.objects.filter(sexo='H').count()
    total_gallos = cantidad_machos + cantidad_hembras

    return render(request, 'index.html', {
        'page_obj': page_obj,
        'sexo_actual': sexo_inicial,
        'cantidad_machos': cantidad_machos,
        'cantidad_hembras': cantidad_hembras,
        'total_gallos': total_gallos,
        'error_eliminacion': error_eliminacion,
    })

def gallo_list_ajax(request):
    sexo = request.GET.get('sexo', 'todos')
    page = request.GET.get('page', 1)

    if sexo == 'machos':
        queryset = Gallo.objects.filter(sexo='M')
    elif sexo == 'hembras':
        queryset = Gallo.objects.filter(sexo='H')
    else:
        queryset = Gallo.objects.all()

    paginator = Paginator(queryset, paginas)
    page_obj = paginator.get_page(page)

    return render(request, 'partials/gallo_list.html', {
        'page_obj': page_obj,
        'sexo_actual': sexo,
    })

def ver(request, idGallo):
    gallo = get_object_or_404(Gallo, idGallo=idGallo)
    hoy = datetime.now().date()

    if gallo.fechaNac is None:
        edadGallo = "Fecha Nac. no establecida"
    else:
        edadGallo = hoy - gallo.fechaNac
        
        anios = edadGallo.days // 365
        meses = (edadGallo.days % 365) // 30
        dias = (edadGallo.days % 365) % 30
        
        edad_texto = []
        
        if anios > 0:
            edad_texto.append(f"{anios} {'año' if anios == 1 else 'años'}")
        
        if meses > 0:
            edad_texto.append(f"{meses} {'mes' if meses == 1 else 'meses'}")
        
        if dias > 0:
            edad_texto.append(f"{dias} {'día' if dias == 1 else 'días'}")
        
        if anios > 0:
            total_meses = anios * 12 + meses
            edad_texto.append(f"({total_meses} {'mes' if total_meses == 1 else 'meses'})")
        
        edadGallo = ', '.join(edad_texto)
    
    return render(request, 'ver.html', {'gallo': gallo, 'edadGallo': edadGallo})
    
def crear(request):
    if request.method == 'POST':
        form = GalloForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                gallo = form.save(commit=False)
                gallo._request = request
                placa_padre = request.POST.get('placaPadre') or None
                placa_madre = request.POST.get('placaMadre') or None

                if placa_padre:
                    gallo.placaPadre_id = placa_padre  # si es FK
                if placa_madre:
                    gallo.placaMadre_id = placa_madre

                gallo.save()
                return redirect('ver', idGallo=gallo.idGallo)

            except Exception as e:
                print("DEBUG - Error saving:", str(e))  # Debug line
                raise
        else:
            print(form.errors)

    else:
        form = GalloForm()

    if form.instance and form.instance.nroPlaca:
        gallos = Gallo.objects.exclude(nroPlaca=form.instance.nroPlaca)
    else:
        gallos = Gallo.objects.all()

    return render(
        request, 'formulario.html', 
        {
            'form': form, 
            'gallos': gallos
            }
        )

def ajax_valida_placa(request):
    placa = request.GET.get('placa', None)
    exists = Gallo.objects.filter(nroPlaca=placa).exists() if placa else False
    return JsonResponse({'exists': exists})

def editar(request, idGallo):
    gallo = get_object_or_404(Gallo, idGallo=idGallo)
    if request.method == 'POST':
        form = GalloForm(request.POST, request.FILES, instance=gallo)
        if form.is_valid():
            placa_padre = request.POST.get('placaPadre') or None
            placa_madre = request.POST.get('placaMadre') or None

            if placa_padre and placa_padre == placa_madre:
                messages.error(request, "Padre y madre no pueden ser el mismo.")
            else:
                gallo = form.save(commit=False)
                gallo._request = request
                gallo.placaPadre_id = placa_padre
                gallo.placaMadre_id = placa_madre
                gallo.save()
                return redirect('ver', idGallo=gallo.idGallo)
    else:
        form = GalloForm(instance=gallo)

    gallos = Gallo.objects.exclude(idGallo=gallo.idGallo)

    contexto = {
        'form': form,
        'gallos': gallos,
        'padre_sel': gallo.placaPadre_id,
        'madre_sel': gallo.placaMadre_id,
    }
    return render(request, 'formulario.html', contexto)

def eliminar(request, idGallo):
    gallo = get_object_or_404(Gallo, idGallo=idGallo)
    try:
        gallo.delete()
    except ProtectedError:
        return redirect(f"{reverse('index')}?error_eliminacion=1")
    return redirect('index')

#encuentros
def crear_encuentro(request):
    if request.method == 'POST':
    
        form = EncuentroForm(request.POST, request.FILES)
        if form.is_valid():
            print("formulario valido")
        else:
            print("errores")
            print(form.errors)

        id_gallo = request.POST.get('gallo')

        if not id_gallo:
            form.add_error(None, "Debe seleccionar un gallo participante.")
        else:
            try:
                gallo = Gallo.objects.get(pk=id_gallo)
            except Gallo.DoesNotExist:
                form.add_error(None, "El gallo seleccionado no existe.")
                gallo = None

            if form.is_valid() and gallo:
                encuentro = form.save(commit=False)
                encuentro._request = request
                encuentro.gallo = gallo
                encuentro.save()
                return redirect('ver_encuentro', pk=encuentro.idEncuentro)
            else:
                print("errores") #no se imprime esto
                print(form.errors)
                print("Gallo: ", gallo)

    else:
        form = EncuentroForm()

    gallos = Gallo.objects.all()
    return render(request, 'encuentros/form_encuentro.html', {
        'form': form,
        'gallos': gallos,
    })

def listar_encuentros(request):
    encuentros = Encuentro.objects.all().order_by('-fechaYHora')
    paginator = Paginator(encuentros, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'encuentros/listar_encuentros.html', {'page_obj': page_obj})

def ver_encuentro(request, pk):
    # Obtener el encuentro con el pk proporcionado
    encuentro = get_object_or_404(Encuentro, pk=pk)

    # Inicializar las variables
    dinero_final = 0
    resultado = encuentro.resultado

    # Obtener los valores que usaremos para los cálculos, asegurándonos de que no sean negativos
    pactada = float(max(encuentro.pactada if encuentro.pactada is not None else 0, 0))
    pago_juez = float(max(encuentro.pago_juez if encuentro.pago_juez is not None else 0, 0))
    apuesta_general = float(max(encuentro.apuesta_general if encuentro.apuesta_general is not None else 0, 0))
    apuesta_por_fuera = float(max(encuentro.apuesta_por_fuera if encuentro.apuesta_por_fuera is not None else 0, 0))
    premio_mayor = float(max(encuentro.premio_mayor if encuentro.premio_mayor is not None else 0, 0))
    porcentaje_premio_mayor = float(max(encuentro.porcentaje_premio_mayor if encuentro.porcentaje_premio_mayor is not None else 0, 0))


    # Calcular el dinero del premio mayor
    dinero_del_premio_mayor = premio_mayor

    # Calcular el total apostado
    todo_el_dinero_apostado = apuesta_general + apuesta_por_fuera

    # Inicializar el dinero después de la apuesta
    dinero_luego_de_la_apuesta = 0


    #pago careador 
    pago_careador = 0

    #gastos 
    gastos = 0

    # Calcular el dinero luego de la apuesta según el resultado
    if resultado == 'V':  # Victoria
        dinero_luego_de_la_apuesta = todo_el_dinero_apostado + dinero_del_premio_mayor

        pago_careador_pollon = premio_mayor * 0.15
        pago_careador_apuesta_general = apuesta_general * (porcentaje_premio_mayor/100)
        pago_careador = pago_careador_pollon + pago_careador_apuesta_general 

        gastos = pago_careador + pago_juez + pactada #+ todo_el_dinero_apostado
        dinero_final = dinero_luego_de_la_apuesta - gastos

    elif resultado == 'T':  # Tablas
        dinero_luego_de_la_apuesta = todo_el_dinero_apostado
        gastos = pactada + todo_el_dinero_apostado
        dinero_final = dinero_luego_de_la_apuesta - gastos
        pago_juez = 0

    elif resultado == 'D':  # Derrota
        gastos = pactada
        dinero_luego_de_la_apuesta = -todo_el_dinero_apostado
        dinero_final = dinero_luego_de_la_apuesta - gastos
        pago_juez = 0
    else:
        raise Exception("Resultado no contemplado: " + resultado)

    # Pasar todos los datos al template
    return render(
        request, 'encuentros/ver_encuentro.html', 
        {
            'encuentro': encuentro,
            'todo_el_dinero_apostado': todo_el_dinero_apostado,
            'pago_careador': pago_careador,
            'dinero_del_premio_mayor': dinero_del_premio_mayor,
            'dinero_luego_de_la_apuesta': dinero_luego_de_la_apuesta,
            'gastos': gastos,
            'dinero_final': dinero_final,
            'pactada': pactada,
            'pago_juez': pago_juez,
            'apuesta_general': apuesta_general,
            'apuesta_por_fuera': apuesta_por_fuera,
            'premio_mayor': premio_mayor,
            'porcentaje_premio_mayor': porcentaje_premio_mayor,
            'resultado': resultado,
        }
    )

def encuentro_form(request, pk=None):
    if pk:
        encuentro = get_object_or_404(Encuentro, pk=pk)
        titulo = "Editar Encuentro #" + str(encuentro.pk)
    else:
        encuentro = None
        titulo = "Nuevo Encuentro"

    if request.method == 'POST':
        print("FILES recibidos:", request.FILES)   
        form = EncuentroForm(request.POST, request.FILES, instance=encuentro)
        id_gallo = request.POST.get('gallo')
        print("ID Gallo:", id_gallo)

        if not form.is_valid():
            print("Errores en el form:", form.errors.as_json()) 
        else:
            print("Form válido")

        if not id_gallo:
            form.add_error(None, "Debe seleccionar un gallo participante.")
        else:
            try:
                gallo = Gallo.objects.get(pk=id_gallo)
            except Gallo.DoesNotExist:
                form.add_error(None, "El gallo seleccionado no existe.")
                gallo = None

            if form.is_valid() and gallo:
                encuentro = form.save(commit=False)
                encuentro.gallo = gallo
                encuentro._request = request
                print("Antes de save():")
                print("video: ", encuentro.video or "No video")
                print("imagen_evento: " , encuentro.imagen_evento)
                encuentro.save()
                print("Después de save():")
                print("video: ", encuentro.video or "No video")
                print("imagen_evento: " , encuentro.imagen_evento)
                return redirect('ver_encuentro', pk=encuentro.idEncuentro)
            else:
                print("Errores en el form:", form.errors.as_json()) 
                print("Gallo: ", gallo)
    else:
        form = EncuentroForm(instance=encuentro)

    gallos = Gallo.objects.all()
    return render(request, 'encuentros/form_encuentro.html', {
        'form': form,
        'gallos': gallos,
        'titulo': titulo,
        'encuentro': encuentro,
    })

def eliminar_encuentro(request, pk):
    encuentro = get_object_or_404(Encuentro, pk=pk)
    encuentro.delete()
    return redirect('listar_encuentros')


#colores
def color_list(request):
    error_eliminacion = False

    # Si es una solicitud POST, se intenta eliminar el color
    if request.method == 'POST' and 'delete_color' in request.POST:
        color_id = request.POST.get('delete_color')
        color = get_object_or_404(Color, pk=color_id)
        try:
            color.delete()
        except ProtectedError:
            return redirect(f"{reverse('color_list')}?error_eliminacion=1")
        return redirect('color_list')

    if request.GET.get('error_eliminacion') == '1':
        error_eliminacion = True

    colores = Color.objects.all()
    return render(request, 'colores/listar_colores.html', {
        'colores': colores,
        'error_eliminacion': error_eliminacion
    })

# Vista para crear un color
def color_create(request):
    if request.method == 'POST':
        form = ColorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('color_list')
    else:
        form = ColorForm()
    return render(request, 'colores/form_color.html', {'form': form})

@csrf_exempt
def color_create_ajax(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({'error': 'El nombre es requerido.'}, status=400)
        if Color.objects.filter(nombre=nombre).exists():
            return JsonResponse({'error': 'Ya existe un color con ese nombre.'}, status=400)
        color = Color.objects.create(nombre=nombre)
        return JsonResponse({'success': True, 'id': color.id, 'nombre': color.nombre})
    return JsonResponse({'error': 'Método no permitido.'}, status=405)

# Vista para editar un color
def color_edit(request, pk):
    color = get_object_or_404(Color, pk=pk)
    if request.method == 'POST':
        form = ColorForm(request.POST, instance=color)
        if form.is_valid():
            form.save()
            return redirect('color_list')
    else:
        form = ColorForm(instance=color)
    return render(request, 'colores/form_color.html', {'form': form})



# estados
def estado_list(request):
    error_eliminacion = False

    if request.method == 'POST' and 'delete_estado' in request.POST:
        estado_id = request.POST.get('delete_estado')
        estado = get_object_or_404(Estado, pk=estado_id)
        try:
            estado.delete()
        except ProtectedError:
            return redirect(f"{reverse('estado_list')}?error_eliminacion=1")
        return redirect('estado_list')

    if request.GET.get('error_eliminacion') == '1':
        error_eliminacion = True

    estados = Estado.objects.all()
    return render(request, 'estados/listar_estados.html', {
        'estados': estados,
        'error_eliminacion': error_eliminacion
    })

# Vista para crear un estado
def estado_create(request):
    if request.method == 'POST':
        form = EstadoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('estado_list')
    else:
        form = EstadoForm()
    return render(request, 'estados/form_estado.html', {'form': form})

@csrf_exempt
def estado_create_ajax(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({'error': 'El nombre es requerido.'}, status=400)
        if Estado.objects.filter(nombre=nombre).exists():
            return JsonResponse({'error': 'Ya existe un estado con ese nombre.'}, status=400)
        estado = Estado.objects.create(nombre=nombre)
        return JsonResponse({'success': True, 'id': estado.id, 'nombre': estado.nombre})
    return JsonResponse({'error': 'Método no permitido.'}, status=405)

# Vista para editar un estado
def estado_edit(request, pk):
    estado = get_object_or_404(Estado, pk=pk)
    if request.method == 'POST':
        form = EstadoForm(request.POST, instance=estado)
        if form.is_valid():
            form.save()
            return redirect('estado_list')
    else:
        form = EstadoForm(instance=estado)
    return render(request, 'estados/form_estado.html', {'form': form})



# galpones
# Vista para listar galpones
def galpon_list(request):
    error_eliminacion = False

    if request.method == 'POST' and 'delete_galpon' in request.POST:
        galpon_id = request.POST.get('delete_galpon')
        galpon = get_object_or_404(Galpon, pk=galpon_id)
        try:
            galpon.delete()
        except ProtectedError:
            return redirect(f"{reverse('galpon_list')}?error_eliminacion=1")
        return redirect('galpon_list')

    if request.GET.get('error_eliminacion') == '1':
        error_eliminacion = True

    galpones = Galpon.objects.all()
    return render(request, 'galpones/listar_galpones.html', {
        'galpones': galpones,
        'error_eliminacion': error_eliminacion
    })

# Vista para crear un galpón
def galpon_create(request):
    if request.method == 'POST':
        form = GalponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('galpon_list')
    else:
        form = GalponForm()
    return render(request, 'galpones/form_galpon.html', {'form': form})

# Vista para crear un galpón con ajax
@csrf_exempt
def galpon_create_ajax(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()

        if not nombre:
            return JsonResponse({'error': 'El nombre es requerido.'}, status=400)

        if Galpon.objects.filter(nombre=nombre).exists():
            return JsonResponse({'error': 'Ya existe un galpón con ese nombre.'}, status=400)

        galpon = Galpon.objects.create(nombre=nombre)
        
        return JsonResponse({
            'success': True,
            'id': galpon.id,
            'nombre': galpon.nombre,
        })

    return JsonResponse({'error': 'Método no permitido.'}, status=405)


# Vista para editar un galpón
def galpon_edit(request, pk):
    galpon = get_object_or_404(Galpon, pk=pk)
    if request.method == 'POST':
        form = GalponForm(request.POST, instance=galpon)
        if form.is_valid():
            form.save()
            return redirect('galpon_list')
    else:
        form = GalponForm(instance=galpon)
    return render(request, 'galpones/form_galpon.html', {'form': form})



# dueños
# Vista para listar los dueños
"""
def dueno_list(request):
    error_eliminacion = False

    if request.method == 'POST' and 'delete_dueno' in request.POST:
        dueno_id = request.POST.get('delete_dueno')
        dueno = get_object_or_404(Dueno, pk=dueno_id)
        try:
            dueno.delete()
        except ProtectedError:
            return redirect(f"{reverse('dueno_list')}?error_eliminacion=1")
        return redirect('dueno_list')

    if request.GET.get('error_eliminacion') == '1':
        error_eliminacion = True

    duenos = Dueno.objects.all()
    return render(request, 'duenos_eventos/listar_duenos.html', {
        'duenos': duenos,
        'error_eliminacion': error_eliminacion
    })

# Vista para crear un dueño
def dueno_create(request):
    if request.method == 'POST':
        form = DuenoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dueno_list')
    else:
        form = DuenoForm()
    return render(request, 'duenos_eventos/form_dueno.html', {'form': form})

@csrf_exempt
def dueno_create_ajax(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({'error': 'El nombre es requerido.'}, status=400)
        if Dueno.objects.filter(nombre=nombre).exists():
            return JsonResponse({'error': 'Ya existe un dueño con ese nombre.'}, status=400)
        dueno = Dueno.objects.create(nombre=nombre)
        return JsonResponse({'success': True, 'id': dueno.id, 'nombre': dueno.nombre})
    return JsonResponse({'error': 'Método no permitido.'}, status=405)

# Vista para editar un dueño
def dueno_edit(request, pk):
    dueno = get_object_or_404(Dueno, pk=pk)
    if request.method == 'POST':
        form = DuenoForm(request.POST, instance=dueno)
        if form.is_valid():
            form.save()
            return redirect('dueno_list')
    else:
        form = DuenoForm(instance=dueno)
    return render(request, 'duenos_eventos/form_dueno.html', {'form': form})

"""


#dueños anteriores:
def duenoanterior_list(request):
    error_eliminacion = False

    # Eliminar dueño anterior
    if request.method == 'POST' and 'delete_duenoanterior' in request.POST:
        duenoanterior_id = request.POST.get('delete_duenoanterior')
        duenoanterior = get_object_or_404(DuenoAnterior, pk=duenoanterior_id)
        try:
            duenoanterior.delete()
        except ProtectedError:
            return redirect(f"{reverse('duenoanterior_list')}?error_eliminacion=1")
        return redirect('duenoanterior_list')

    if request.GET.get('error_eliminacion') == '1':
        error_eliminacion = True

    duenosanteriores = DuenoAnterior.objects.all()
    return render(request, 'duenos_anteriores/listar_duenosanteriores.html', {
        'duenosanteriores': duenosanteriores,
        'error_eliminacion': error_eliminacion
    })

# Vista para crear un nuevo dueño anterior
def duenoanterior_create(request):
    if request.method == 'POST':
        form = DuenoAnteriorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('duenoanterior_list')
    else:
        form = DuenoAnteriorForm()
    return render(request, 'duenos_anteriores/form_duenoanterior.html', {'form': form})

@csrf_exempt
def duenoanterior_create_ajax(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({'error': 'El nombre es requerido.'}, status=400)
        if DuenoAnterior.objects.filter(nombre=nombre).exists():
            return JsonResponse({'error': 'Ya existe un dueño anterior con ese nombre.'}, status=400)
        dueno_anterior = DuenoAnterior.objects.create(nombre=nombre)
        return JsonResponse({'success': True, 'id': dueno_anterior.id, 'nombre': dueno_anterior.nombre})
    return JsonResponse({'error': 'Método no permitido.'}, status=405)

# Vista para editar un dueño anterior
def duenoanterior_edit(request, pk):
    duenoanterior = get_object_or_404(DuenoAnterior, pk=pk)
    if request.method == 'POST':
        form = DuenoAnteriorForm(request.POST, instance=duenoanterior)
        if form.is_valid():
            form.save()
            return redirect('duenoanterior_list')
    else:
        form = DuenoAnteriorForm(instance=duenoanterior)
    return render(request, 'duenos_anteriores/form_duenoanterior.html', {'form': form})