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
from django.db.models import F
import mimetypes
from django.template.loader import render_to_string
import boto3
from botocore.exceptions import ClientError
import time
from django.conf import settings

LIMITE_MB_ARCHIVO = 2000

def generate_presigned_put(field_name, folder, filename, content_type, file_size):
    s3 = boto3.client(
        service_name=settings.R2_SERVICE_NAME,
        region_name=settings.R2_REGION,
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY,
        aws_secret_access_key=settings.R2_SECRET_KEY
    )

    timestamp = int(time.time())
    name_no_tildes = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')
    safe_name = name_no_tildes.replace(' ', '_')
    key = f"{folder}/{timestamp}_{safe_name}" if folder else f"{timestamp}_{safe_name}"

    params = {
        'Bucket': settings.R2_BUCKET_NAME,
        'Key': key,
        'ACL': 'public-read',
        'ContentType': content_type,
        'ContentLength': file_size
    }

    try:
        presigned_url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params=params,
            ExpiresIn=3600  # 1 hora
        )
        return {'url': presigned_url, 'key': key, 'field_name': field_name}
    except ClientError as e:
        print(f"Error generating presigned PUT: {e}")
        return None

@csrf_exempt
def get_presigned_put(request):
    if request.method == 'POST':
        field_name = request.POST.get('field_name')
        folder = request.POST.get('folder', 'gll/encuentros')
        filename = request.POST.get('filename')
        content_type = request.POST.get('content_type')
        file_size = int(request.POST.get('file_size', 0))

        if file_size > LIMITE_MB_ARCHIVO * 1024 * 1024:
            return JsonResponse({'error': f'El archivo excede el límite de {LIMITE_MB_ARCHIVO} MB.'}, status=400)

        if not all([field_name, filename, content_type]):
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        presigned = generate_presigned_put(field_name, folder, filename, content_type, file_size)
        if presigned:
            return JsonResponse(presigned)
        else:
            return JsonResponse({'error': 'Failed to generate presigned URL'}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)

def filtros(request):
    columna = request.GET.get('columna', '')
    valor = request.GET.get('valor', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    page = request.GET.get('page', 1)

    queryset = Gallo.objects.all().order_by(F('nroPlaca_id').asc(nulls_last=True))

    # Diccionario para mapear columna a filtro
    filtros_map = {
        'nroPlaca': 'nroPlaca__nroPlaca__icontains',
        'color': 'color__nombre__icontains',
        'sexo': 'sexo__icontains',
        'tipoGallo': 'tipoGallo__icontains',
        'peso': 'peso__peso__icontains',
        'nroPlacaAnterior': 'nroPlacaAnterior__nroPlaca__icontains',
        'nombreDuenoAnterior': 'nombreDuenoAnterior__nombre__icontains',
        'estadoDeSalud': 'estadoDeSalud__nombre__icontains',
    }

    if columna in ['fechaNac', 'fechaMuerte'] and (fecha_desde or fecha_hasta):
        if fecha_desde:
            filtro = {f'{columna}__gte': fecha_desde}
            queryset = queryset.filter(**filtro)
        if fecha_hasta:
            filtro = {f'{columna}__lte': fecha_hasta}
            queryset = queryset.filter(**filtro)
    elif columna and valor and columna in filtros_map:
        filtro = {filtros_map[columna]: valor}
        queryset = queryset.filter(**filtro)

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(page)

    return render(request, 'filtros.html', {
        'page_obj': page_obj,
        'columna': columna,
        'valor': valor,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
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
        queryset = Gallo.objects.order_by(F('nroPlaca_id').asc(nulls_last=True))
    else:
        queryset = Gallo.objects.filter(sexo=sexo_inicial).order_by(F('nroPlaca_id').asc(nulls_last=True))

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
        queryset = Gallo.objects.filter(sexo='M').order_by(F('nroPlaca_id').asc(nulls_last=True))
    elif sexo == 'hembras':
        queryset = Gallo.objects.filter(sexo='H').order_by(F('nroPlaca_id').asc(nulls_last=True))
    else:
        queryset = Gallo.objects.all().order_by(F('nroPlaca_id').asc(nulls_last=True))

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

@csrf_exempt
def upload_archivo_adicional(request, idGallo):
    """Vista AJAX para subir archivos adicionales"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        gallo = Gallo.objects.get(pk=idGallo)
        action = request.POST.get('action', 'get_presigned')

        if action == 'get_presigned':
            # Paso 1: Devolver presigned URL
            filename = request.POST.get('filename')
            content_type = request.POST.get('content_type')
            file_size = int(request.POST.get('file_size', 0))

            if file_size > LIMITE_MB_ARCHIVO * 1024 * 1024:
                return JsonResponse({'error': f'El archivo excede el límite de {LIMITE_MB_ARCHIVO} MB.'}, status=400)

            if not all([filename, content_type]):
                return JsonResponse({'error': 'Faltan parámetros'}, status=400)

            # Determinar tipo
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                if mime_type.startswith('image/'):
                    tipo = 'imagen'
                elif mime_type.startswith('video/'):
                    tipo = 'video'
                else:
                    return JsonResponse({'error': 'Tipo de archivo no permitido'}, status=400)
            else:
                ext = filename.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                    tipo = 'imagen'
                elif ext in ['mp4', 'avi', 'mov', 'webm', 'mkv']:
                    tipo = 'video'
                else:
                    return JsonResponse({'error': 'Tipo de archivo no reconocido'}, status=400)

            presigned = generate_presigned_put(
                field_name='archivo',
                folder='gll/archivos_adicionales',
                filename=filename,
                content_type=content_type,
                file_size=file_size
            )
            if presigned:
                return JsonResponse({**presigned, 'tipo': tipo})
            else:
                return JsonResponse({'error': 'No se pudo generar la URL presignada'}, status=500)

        elif action == 'confirm':
            # Paso 2: Crear registro tras upload exitoso
            key = request.POST.get('key')
            tipo = request.POST.get('tipo')
            nombre = request.POST.get('nombre')

            if not all([key, tipo, nombre]):
                return JsonResponse({'error': 'Faltan parámetros para confirmar'}, status=400)

            archivo_adicional = ArchivosAdicionales()
            archivo_adicional.content_object = gallo
            archivo_adicional.tipo = tipo
            archivo_adicional.archivo = key
            archivo_adicional.save()

            return JsonResponse({
                'success': True,
                'id': archivo_adicional.id,
                'url': archivo_adicional.archivo,
                'tipo': tipo,
                'nombre': nombre
            })

    except Gallo.DoesNotExist:
        return JsonResponse({'error': 'Gallo no encontrado'}, status=404)
    except Exception as e:
        print(f"DEBUG - Error en upload_archivo_adicional: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def delete_archivo_adicional(request, archivo_id):
    """Vista AJAX para eliminar archivos adicionales"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        archivo = ArchivosAdicionales.objects.get(pk=archivo_id)
        archivo.delete()
        return JsonResponse({'success': True})
    except ArchivosAdicionales.DoesNotExist:
        return JsonResponse({'error': 'Archivo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

registros_por_pagina = 6

def padres_modal_content(request):
    page = request.GET.get('page_padres', 1)
    buscar = request.GET.get('buscar')
    placa_none = request.GET.get('placa_none')
    queryset = Gallo.objects.filter(sexo='M').order_by('nroPlaca')

    if buscar is not None:
        queryset = queryset.filter(nroPlaca__nroPlaca__icontains=buscar)
    if placa_none is not None:
        queryset = queryset.filter(nroPlaca__isnull=True)

    paginator = Paginator(queryset, registros_por_pagina)
    padres = paginator.get_page(page)
    html = render_to_string('gll_app/padres_modal_content.html', {'padres': padres})
    return JsonResponse({'html': html})

def madres_modal_content(request):
    page = request.GET.get('page_madres', 1)
    buscar = request.GET.get('buscar')
    placa_none = request.GET.get('placa_none')
    queryset = Gallo.objects.filter(sexo='H').order_by('nroPlaca')

    if buscar is not None:
        queryset = queryset.filter(nroPlaca__nroPlaca__icontains=buscar)
    if placa_none is not None:
        queryset = queryset.filter(nroPlaca__isnull=True)

    paginator = Paginator(queryset, registros_por_pagina)
    madres = paginator.get_page(page)
    html = render_to_string('gll_app/madres_modal_content.html', {'madres': madres})
    return JsonResponse({'html': html})

@csrf_exempt
def update_nombre_img(request, idGallo):
    if request.method == 'POST':
        gallo = get_object_or_404(Gallo, idGallo=idGallo)
        key = request.POST.get('key')
        if key:
            gallo.nombre_img = key
            gallo.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'No key provided'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

def crear(request):
    #print("DEBUG - Método de la solicitud:", request.method)

    if request.method == 'POST':
        #print("DEBUG - CONTENT_TYPE:", request.META.get('CONTENT_TYPE'))
        #print("DEBUG - Datos POST recibidos:", request.POST)

        form = GalloForm(request.POST, request.FILES)

        if 'nombre_img' not in request.FILES:
            form.fields['nombre_img'].required = False
            #print("DEBUG - No recibí nombre_img en request.FILES -> campo no requerido temporalmente")


        if form.is_valid():
            #print("DEBUG - El formulario es válido.")

            try:
                gallo = form.save(commit=False)
                gallo._request = request

                placa_padre = request.POST.get('placaPadre') or None
                placa_madre = request.POST.get('placaMadre') or None

                #print("DEBUG - placaPadre:", placa_padre)
                #print("DEBUG - placaMadre:", placa_madre)

                if placa_padre:
                    gallo.placaPadre_id = placa_padre
                if placa_madre:
                    gallo.placaMadre_id = placa_madre

                gallo.save()

                #print("DEBUG - Gallo guardado con ID:", gallo.idGallo)

                response_data = {
                    'success': True,
                    'idGallo': gallo.idGallo,
                    'redirect': reverse('ver', kwargs={'idGallo': gallo.idGallo})
                }
                return JsonResponse(response_data)

            except Exception as e:
                #print("DEBUG - Error al guardar el gallo:", str(e))
                #import traceback
                #traceback.print_exc()  # Imprime traza completa del error
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        else:
            #print("DEBUG - Formulario inválido:", form.errors.as_json())
            return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)

    else:
        #print("DEBUG - Solicitud GET recibida.")
        form = GalloForm()

    return render(
        request, 'formulario.html',
        {
            'form': form,
        }
    )

def ajax_valida_placa(request):
    placa = request.GET.get('placa', None)
    exists = Gallo.objects.filter(nroPlaca=placa).exists() if placa else False
    return JsonResponse({'exists': exists})

def editar(request, idGallo):
    #print("ejecutando editar")
    gallo = get_object_or_404(Gallo, idGallo=idGallo)
    
    #print("DEBUG - Método HTTP:", request.method)

    if request.method == 'POST':
        #print("DEBUG - Se recibió un POST.")
        #print("DEBUG - Archivos recibidos:", request.FILES)
        #print("DEBUG - POST data:", request.POST)

        # ¡IMPORTANTE! Asegúrate de pasar también request.FILES
        form = GalloForm(request.POST, request.FILES, instance=gallo)

        if form.is_valid():
            #print("DEBUG - Formulario válido.")

            placa_padre = request.POST.get('placaPadre') or None
            placa_madre = request.POST.get('placaMadre') or None

            #print(f"DEBUG - placaPadre: {placa_padre}, placaMadre: {placa_madre}")

            if placa_padre and placa_padre == placa_madre:
                #print("ERROR - Padre y madre son iguales.")
                messages.error(request, "Padre y madre no pueden ser el mismo.")
            else:
                gallo = form.save(commit=False)
                gallo._request = request  # ¿Lo necesitas para algún procesamiento posterior?
                gallo.placaPadre_id = placa_padre
                gallo.placaMadre_id = placa_madre

                if 'nombre_img_key' in request.POST:
                    gallo.nombre_img = request.POST['nombre_img_key']

                gallo.save()
                #print("DEBUG - Gallo guardado correctamente. Redirigiendo.")
                return redirect('ver', idGallo=gallo.idGallo)
        else:
            #print("ERROR - Formulario inválido.")
            print("Errores:", form.errors.as_json())

        form = GalloForm(instance=gallo)

    # Datos adicionales para contexto
    placa_padre = obtener_placa_madre_padre(gallo.idGallo, 'padre')
    placa_madre = obtener_placa_madre_padre(gallo.idGallo, 'madre')

    archivos_adicionales = gallo.archivos_adicionales.all()
    archivos_imagenes = archivos_adicionales.filter(tipo='imagen')
    archivos_videos = archivos_adicionales.filter(tipo='video')

    contexto = {
        'form': form,
        'padre_sel': gallo.placaPadre_id,
        'madre_sel': gallo.placaMadre_id,
        'placa_padre': placa_padre,
        'placa_madre': placa_madre,
        'placa_padre_is_false': placa_padre is False,
        'placa_madre_is_false': placa_madre is False,
        'archivos_imagenes': archivos_imagenes,
        'archivos_videos': archivos_videos,
    }

    #print("DEBUG - Renderizando formulario con contexto.")
    return render(request, 'formulario.html', contexto)

def obtener_placa_madre_padre(id_hijo, pariente):
    try:
        hijo = Gallo.objects.select_related('placaPadre__nroPlaca', 'placaMadre__nroPlaca').get(pk=id_hijo)

        if pariente == 'padre':
            if hijo.placaPadre is None:
                return False  # No hay padre asignado
            return hijo.placaPadre.nroPlaca if hijo.placaPadre.nroPlaca else None

        elif pariente == 'madre':
            if hijo.placaMadre is None:
                return False  # No hay madre asignada
            return hijo.placaMadre.nroPlaca if hijo.placaMadre.nroPlaca else None

        else:
            raise ValueError("El parámetro 'pariente' debe ser 'padre' o 'madre'.")

    except Gallo.DoesNotExist:
        return None  # El hijo no existe

def eliminar(request, idGallo):
    gallo = get_object_or_404(Gallo, idGallo=idGallo)
    try:
        gallo.delete()
    except ProtectedError:
        return redirect(f"{reverse('index')}?error_eliminacion=1")
    return redirect('index')

#encuentros
def participantes_modal_content(request):
    page = request.GET.get('page_participantes', 1)
    buscar = request.GET.get('buscar')
    placa_none = request.GET.get('placa_none')
    id_actual = request.GET.get('id_actual')

    queryset = Gallo.objects.all().order_by('nroPlaca')
    if id_actual:
        queryset = queryset.exclude(idGallo=id_actual)
    if buscar is not None:
        queryset = queryset.filter(nroPlaca__nroPlaca__icontains=buscar)
    if placa_none is not None:
        queryset = queryset.filter(nroPlaca__isnull=True)

    paginator = Paginator(queryset, registros_por_pagina)
    participantes = paginator.get_page(page)
    html = render_to_string('gll_app/participantes_modal_content.html', {'participantes': participantes})
    return JsonResponse({'html': html})

def crear_encuentro(request):
    if request.method == 'POST':
    
        form = EncuentroForm(request.POST, request.FILES)
        if form.is_valid():
            print("formulario valido")
        else:
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
                if 'video_key' in request.POST:
                    encuentro.video = request.POST['video_key']
                if 'imagen_evento_key' in request.POST:
                    encuentro.imagen_evento = request.POST['imagen_evento_key']
                encuentro.save()
                return redirect('ver_encuentro', pk=encuentro.idEncuentro)
            else:
                #print("errores") #no se imprime esto
                print(form.errors)
                #print("Gallo: ", gallo)

    else:
        form = EncuentroForm()

    gallos = Gallo.objects.all().order_by(F('nroPlaca_id').asc(nulls_last=True))
    return render(request, 'encuentros/form_encuentro.html', {
        'form': form,
        'gallos': gallos,
    })

def listar_encuentros(request):
    encuentros = Encuentro.objects.all().order_by('-fechaYHora')
    paginator = Paginator(encuentros, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_victorias = sum(1 for e in encuentros if e.resultado == 'V')
    total_tablas = sum(1 for e in encuentros if e.resultado == 'T')
    total_derrotas = sum(1 for e in encuentros if e.resultado == 'D')
    total = total_victorias + total_tablas + total_derrotas

    
    def porcentaje(valor, total):
        return round((valor / total * 100), 2) if total > 0 else 0

    return render(request, 'encuentros/listar_encuentros.html', {
        'page_obj': page_obj,
        'total_victorias': total_victorias,
        'total_tablas': total_tablas,
        'total_derrotas': total_derrotas,
        'porcentaje_victorias': porcentaje(total_victorias, total),
        'porcentaje_tablas': porcentaje(total_tablas, total),
        'porcentaje_derrotas': porcentaje(total_derrotas, total),
    })

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
        #print("FILES recibidos:", request.FILES)   
        form = EncuentroForm(request.POST, request.FILES, instance=encuentro)
        id_gallo = request.POST.get('gallo')
        #print("ID Gallo:", id_gallo)

        if not form.is_valid():
            print("Errores en el form:", form.errors.as_json()) 

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
                #print("Manejando keys:")
                if 'video_key' in request.POST:
                    encuentro.video = request.POST['video_key']
                if 'imagen_evento_key' in request.POST:
                    encuentro.imagen_evento = request.POST['imagen_evento_key']
                #print("Antes de save():")
                #print("video: ", encuentro.video or "No video")
                #print("imagen_evento: " , encuentro.imagen_evento)
                encuentro.save()
                #print("Después de save():")
                #print("video: ", encuentro.video or "No video")
                #print("imagen_evento: " , encuentro.imagen_evento)
                return redirect('ver_encuentro', pk=encuentro.idEncuentro)
            else:
                print("Errores en el form:", form.errors.as_json()) 
                #print("Gallo: ", gallo)
    else:
        form = EncuentroForm(instance=encuentro)

    gallos = Gallo.objects.all().order_by(F('nroPlaca_id').asc(nulls_last=True))
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