from django.db import models
import time
import os
from django.core.validators import MinValueValidator
import requests
from django.conf import settings
from django.core.files.base import ContentFile
import base64
import time
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

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
    
    archivo = ImageKitField(folder='gll/archivos_adicionales', null=False)
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
    nombre_img = ImageKitField(folder='gll/gallos')
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
    video = ImageKitField(folder='gll/encuentros', null=True)
    condicionGallo = models.ForeignKey(Estado, on_delete=models.PROTECT)
    #duenoEvento = models.ForeignKey(Dueno, on_delete=models.PROTECT)
    imagen_evento = ImageKitField(folder='gll/encuentros', null=True)

    # gastos fijos
    pactada = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])
    pago_juez = models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True)

    # ganancias
    apuesta_general = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
    premio_mayor = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])
    porcentaje_premio_mayor = models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[MinValueValidator(0)])
    apuesta_por_fuera = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])
