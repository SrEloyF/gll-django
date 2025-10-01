from django.db import models
import time
import os
from django.core.validators import MinValueValidator
import requests
from django.conf import settings
import base64
import time
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.dispatch import receiver
from django.db.models.signals import post_delete
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
import unicodedata
from urllib.parse import urlparse

os.getenv('R2_ACCOUNT_ID')
os.getenv('R2_NOMBRE_BUCKET')
os.getenv('R2_ACCESS_KEY')
os.getenv('R2_SECRET_KEY')
os.getenv('R2_AWS_REGION')
os.getenv('R2_SERVICE_NAME')

load_dotenv()
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_BUCKET = os.getenv('R2_NOMBRE_BUCKET')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY')
R2_SECRET_KEY = os.getenv('R2_SECRET_KEY')
R2_REGION = os.getenv('R2_AWS_REGION')
R2_SERVICE = os.getenv('R2_SERVICE_NAME', 's3')
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
R2_URL_BASE = os.getenv('R2_URL_BASE')

class CloudflareR2Field(models.CharField):
    def __init__(self, folder=None, *args, **kwargs):
        self.folder = folder
        kwargs['max_length'] = 500
        super().__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        # Registrar el nombre del atributo
        super().contribute_to_class(cls, name, **kwargs)
        # Conectar post_delete para eliminar del R2 cuando se borre la instancia
        post_delete.connect(self._post_delete, sender=cls, weak=False)

    def _post_delete(self, sender, instance, **kwargs):
        try:
            self.delete_from_r2(instance)
        except Exception as e:
            print(f"DEBUG - Error deleting on post_delete: {e}")

    def _extract_key(self, value):
        """Devuelve la key en R2 a partir de una URL o de la key guardada."""
        if not value:
            return None
        if isinstance(value, str) and value.startswith('http'):
            if R2_URL_BASE in value:
                return value.replace(f"https://{R2_URL_BASE}/", "")
            else:
                path = urlparse(value).path
                return path.lstrip('/')
        return value

    def _delete_key_from_r2(self, key):
        if not key:
            return
        try:
            s3 = boto3.client(
                R2_SERVICE,
                region_name=R2_REGION,
                endpoint_url=R2_ENDPOINT,
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY
            )
            s3.delete_object(Bucket=R2_BUCKET, Key=key)
            print(f"DEBUG - Deleted {key} from R2")
        except Exception as e:
            print(f"DEBUG - Error deleting {key} from R2: {e}")

    def pre_save(self, model_instance, add):
        """
        Pre-save que:
         - detecta archivo subido en request.FILES (prioritario),
         - sube nuevo archivo si hay uno,
         - elimina el antiguo archivo si corresponde (y no está referenciado por otra fila),
         - si el campo se vacía, borra el antiguo.
        """
        # Obtener valor actualmente asignado en la instancia (puede ser key o URL)
        current_value = getattr(model_instance, self.attname)

        # Obtener el valor antiguo directamente de la base de datos (si existe)
        old_db_value = None
        if getattr(model_instance, 'pk', None):
            try:
                qs = model_instance.__class__._default_manager.filter(pk=model_instance.pk).values_list(self.attname, flat=True)
                old_db_value = qs.first()
            except Exception as e:
                print(f"DEBUG - no pude leer old_db_value: {e}")

        old_key = self._extract_key(old_db_value)

        # Obtener request y archivo subido (si existe)
        req = getattr(model_instance, '_request', None)
        uploaded_file = None
        if req is not None:
            uploaded = req.FILES.get(self.attname)
            if not uploaded:
                uploaded_list = req.FILES.getlist(self.attname)
                if uploaded_list:
                    uploaded = uploaded_list[0]
            uploaded_file = uploaded

        # Caso: el usuario limpió el campo (ej. '') -> borrar antiguo si existe
        if not uploaded_file and (current_value in [None, ""]):
            if old_key:
                # comprobar si otra fila usa la misma referencia antes de borrar
                other_refs = model_instance.__class__._default_manager.filter(**{self.attname: old_db_value}).exclude(pk=model_instance.pk).exists()
                if not other_refs:
                    self._delete_key_from_r2(old_key)
                else:
                    print(f"DEBUG - No se borra {old_key}: está referenciada por otra fila.")
            # almacenar vacío en DB
            model_instance.__dict__[self.attname] = ""
            return ""

        # Si hay archivo subido, proceder a subirlo (reemplazo)
        if uploaded_file and hasattr(uploaded_file, 'read'):
            try:
                print(f"DEBUG - Tamaño del archivo recibido: {uploaded_file.size / 1024:.2f} KB")
                timestamp = int(time.time())
                original_name = getattr(uploaded_file, 'name', f'file_{timestamp}')
                name_no_tildes = unicodedata.normalize('NFKD', original_name).encode('ASCII', 'ignore').decode('ASCII')
                safe_name = name_no_tildes.replace(' ', '_')
                filename = f"{timestamp}_{safe_name}"
                key = f"{self.folder}/{filename}" if self.folder else filename

                s3 = boto3.client(
                    R2_SERVICE,
                    region_name=R2_REGION,
                    endpoint_url=R2_ENDPOINT,
                    aws_access_key_id=R2_ACCESS_KEY,
                    aws_secret_access_key=R2_SECRET_KEY
                )

                uploaded_file.seek(0)
                content_type = getattr(uploaded_file, 'content_type', 'application/octet-stream')
                s3.upload_fileobj(uploaded_file, R2_BUCKET, key, ExtraArgs={"ACL": "public-read", "ContentType": content_type})

                # almacenar la key en la instancia (para guardar en DB)
                model_instance.__dict__[self.attname] = key

                print(f"DEBUG - Uploaded to R2, key: {key}")

                # borrar antiguo si existe y no está referenciado por otra fila
                if old_key and old_key != key:
                    # comparamos el valor tal cual que vive en la DB (old_db_value)
                    other_refs = model_instance.__class__._default_manager.filter(**{self.attname: old_db_value}).exclude(pk=model_instance.pk).exists()
                    if not other_refs:
                        self._delete_key_from_r2(old_key)
                    else:
                        print(f"DEBUG - No se borra {old_key}: está referenciada por otra fila.")

                return key

            except ClientError as e:
                print(f"DEBUG - R2 upload error: {e}")
                raise
            except Exception as e:
                print(f"DEBUG - Exception occurred: {str(e)}")
                raise

        # Si llegamos aquí sin archivo subido, devolver el valor actual (puede ser URL o key)
        # Normalmente Django llamará a get_prep_value después para guardar la representación correcta.
        return current_value

    # __get__, __set__, to_python, from_db_value, get_prep_value, delete_from_r2
    # puedes mantener las versiones que ya tenías; aquí solo debes asegurarte de que
    # get_prep_value guarde la key (no la URL) y __get__ construya la URL pública.
    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance.__dict__.get(self.attname)
        if not value:
            return ""
        if isinstance(value, str) and value.startswith('http'):
            return value
        return f"https://{R2_URL_BASE}/{value}"

    def __set__(self, instance, value):
        if value and isinstance(value, str) and value.startswith('http'):
            if R2_URL_BASE in value:
                value = value.replace(f"https://{R2_URL_BASE}/", "")
        instance.__dict__[self.attname] = value

    def to_python(self, value):
        if not value:
            return ""
        if isinstance(value, str) and value.startswith('http'):
            return value
        return f"https://{R2_URL_BASE}/{value}" if value else ""

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        if not value:
            return ""
        if isinstance(value, str) and value.startswith('http'):
            if R2_URL_BASE in value:
                return value.replace(f"https://{R2_URL_BASE}/", "")
        return value

    def delete_from_r2(self, instance):
        """Método público que borra la key actual asociada a una instancia."""
        raw_value = instance.__dict__.get(self.attname) or getattr(instance, self.attname, None)
        # extraer key si viene con URL
        key = self._extract_key(raw_value)
        if key:
            self._delete_key_from_r2(key)

class ImageKitField(models.CharField):
    def __init__(self, folder=None, *args, **kwargs):
        self.folder = folder
        kwargs['max_length'] = 500
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        file = getattr(model_instance, self.attname)
        print(f"DEBUG - Pre save called for {self.attname}")
        print(f"DEBUG - File type: {type(file)}")
        print(f"DEBUG - File value: {file}")

        if not file:
            return file

        # Si es una URL de ImageKit, no procesar
        if isinstance(file, str) and file.startswith('http'):
            return file

        # Si es un string pero no es URL, probablemente sea un archivo nuevo
        if isinstance(file, str):
            # Buscar el archivo en request.FILES
            file_obj = model_instance._request.FILES.get(self.attname)
            if file_obj:
                file = file_obj

        # Procesar el archivo
        if hasattr(file, 'read'):
            try:
                timestamp = int(time.time())
                filename = f"{timestamp}_{file.name}"
                
                files = {
                    'file': (filename, file, file.content_type)
                }
                
                data = {
                    'fileName': filename,
                    'folder': self.folder
                }

                auth = base64.b64encode(f"{settings.IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
                headers = {
                    'Authorization': f'Basic {auth}'
                }

                print(f"DEBUG - Making request to ImageKit")
                print(f"DEBUG - Headers: {headers}")
                print(f"DEBUG - Data: {data}")

                response = requests.post(
                    'https://api.imagekit.io/v1/files/upload',
                    files=files,
                    data=data,
                    headers=headers
                )

                print(f"DEBUG - Response status: {response.status_code}")
                print(f"DEBUG - Response body: {response.text}")

                if response.status_code == 200:
                    result = response.json()
                    url = result['url']
                    return url
                else:
                    raise Exception(f"Failed to upload to ImageKit: {response.text}")
            except Exception as e:
                print(f"DEBUG - Exception occurred: {str(e)}")
                raise

        return file

"""
def imagen_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{int(time.time())}.{ext}"
    return os.path.join('gallos', filename)

def imagen_upload_path_encuentros(instance, filename):
    base, ext = os.path.splitext(filename)
    timestamp = int(time.time())
    return f"encuentros/{timestamp}_{base}{ext}"
"""

class Color(models.Model):
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)

    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre
    
class Estado(models.Model):
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)

    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

"""   
class Dueno(models.Model):
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)

    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre
"""
    
class Galpon(models.Model):
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)

    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre
    
class DuenoAnterior(models.Model):
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)
        
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

class PlacaCheck(models.Model):
    nroPlaca = models.AutoField(primary_key=True)
    def __str__(self):
        return str(self.nroPlaca)

class PesosCheck(models.Model):
    peso = models.DecimalField(unique=True, decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
    def __str__(self):
        return str(self.peso)

class ArchivosAdicionales(models.Model):
    TIPO_ARCHIVO = [
        ('imagen', 'Imagen'),
        ('video', 'Video')
    ]
    
    archivo = CloudflareR2Field(folder='gll/archivos_adicionales', null=False)
    tipo = models.CharField(max_length=6, choices=TIPO_ARCHIVO)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Archivo adicional"
        verbose_name_plural = "Archivos adicionales"
    
    def __str__(self):
        return f"Archivo {self.tipo} para {self.content_object}"

class Gallo(models.Model):
    idGallo = models.AutoField(primary_key=True)
    nroPlaca = models.ForeignKey(PlacaCheck, null=True, blank=False, on_delete=models.PROTECT, related_name='gallo_por_placa')
    fechaNac = models.DateField(null=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT)
    sexo = models.CharField(max_length=1, choices=[('M', 'Macho'), ('H', 'Hembra')])
    tipoGallo = models.CharField(max_length=20, choices=[
        ('DP', 'Gallo De Pelea'),
        ('PADRE', 'Gallo Padre'),
        ('MADRE', 'Gallina Madre')
    ])

    peso = models.ForeignKey(PesosCheck, on_delete=models.PROTECT, null=True)
    nroPlacaAnterior = models.ForeignKey(PlacaCheck, null=True, blank=False, on_delete=models.PROTECT, related_name='gallo_por_placa_anterior')
    nombreDuenoAnterior = models.ForeignKey(DuenoAnterior, on_delete=models.PROTECT, null=True)
    estadoDeSalud = models.ForeignKey(Estado, on_delete=models.PROTECT)
    fechaMuerte = models.DateField(null=True, blank=False)

    #observaciones = models.TextField()
    nombre_img = CloudflareR2Field(folder='gll/gallos')
    placaPadre = models.ForeignKey('self', null=True, blank=False, on_delete=models.SET_NULL, related_name='hijos_padre')
    placaMadre = models.ForeignKey('self', null=True, blank=False, on_delete=models.SET_NULL, related_name='hijos_madre')
    archivos_adicionales = GenericRelation(ArchivosAdicionales)

    def __str__(self):
        return f"Gallo {self.nroPlaca if self.nroPlaca is not None else 'S.P.'}"

class Encuentro(models.Model):
    idEncuentro = models.AutoField(primary_key=True)
    fechaYHora = models.DateField(null=False)
    galpon1 = models.ForeignKey(Galpon, on_delete=models.PROTECT, related_name='galpon1')
    galpon2 = models.ForeignKey(Galpon, on_delete=models.PROTECT, related_name='galpon2')
    gallo = models.ForeignKey(Gallo, on_delete=models.PROTECT)
    resultado = models.CharField(max_length=20, choices=[
        ('V', 'Victoria'),
        ('T', 'Tablas'),
        ('D', 'Derrota')
    ], default='V')
    video = CloudflareR2Field(folder='gll/encuentros', null=True)
    condicionGallo = models.ForeignKey(Estado, on_delete=models.PROTECT)
    #duenoEvento = models.ForeignKey(Dueno, on_delete=models.PROTECT)
    imagen_evento = CloudflareR2Field(folder='gll/encuentros', null=True)

    # gastos fijos
    pactada = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])
    pago_juez = models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True)

    # ganancias
    apuesta_general = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
    premio_mayor = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])
    porcentaje_premio_mayor = models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[MinValueValidator(0)])
    apuesta_por_fuera = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])

@receiver(post_delete)
def delete_r2_files(sender, instance, **kwargs):
    for field in sender._meta.get_fields():
        if isinstance(field, CloudflareR2Field):
            field.delete_from_r2(instance)