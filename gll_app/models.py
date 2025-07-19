from django.db import models
import time
import os
from django.core.validators import MinValueValidator

def imagen_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{int(time.time())}.{ext}"
    return os.path.join('gallos', filename)

def imagen_upload_path_encuentros(instance, filename):
    base, ext = os.path.splitext(filename)
    timestamp = int(time.time())
    return f"encuentros/{timestamp}_{base}{ext}"

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

class Gallo(models.Model):
    idGallo = models.AutoField(primary_key=True)
    nroPlaca = models.ForeignKey(PlacaCheck, null=True, blank=False, on_delete=models.PROTECT, related_name='gallo_por_placa')
    fechaNac = models.DateField(null=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT)
    sexo = models.CharField(max_length=1, choices=[('M', 'Macho'), ('H', 'Hembra')])
    tipoGallo = models.CharField(max_length=20, choices=[
        ('DP', 'Gallo De Pelea'),
        ('PADRE', 'Gallo Padre'),
        ('MADRE', 'Gallina madre')
    ])

    peso = models.ForeignKey(PesosCheck, on_delete=models.PROTECT, null=True)
    nroPlacaAnterior = models.ForeignKey(PlacaCheck, null=True, blank=False, on_delete=models.PROTECT, related_name='gallo_por_placa_anterior')
    nombreDuenoAnterior = models.ForeignKey(DuenoAnterior, on_delete=models.PROTECT, null=True)
    estadoDeSalud = models.ForeignKey(Estado, on_delete=models.PROTECT)
    fechaMuerte = models.DateField(null=True, blank=False)

    #observaciones = models.TextField()
    nombre_img = models.ImageField(upload_to=imagen_upload_path)
    placaPadre = models.ForeignKey('self', null=True, blank=False, on_delete=models.SET_NULL, related_name='hijos_padre')
    placaMadre = models.ForeignKey('self', null=True, blank=False, on_delete=models.SET_NULL, related_name='hijos_madre')

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
    video = models.FileField(upload_to=imagen_upload_path, null=True)
    condicionGallo = models.ForeignKey(Estado, on_delete=models.PROTECT)
    #duenoEvento = models.ForeignKey(Dueno, on_delete=models.PROTECT)
    imagen_evento = models.ImageField(upload_to=imagen_upload_path_encuentros, null=True)

    # gastos fijos
    pactada = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])
    pago_juez = models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True)

    # ganancias
    apuesta_general = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
    premio_mayor = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])
    porcentaje_premio_mayor = models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[MinValueValidator(0)])
    apuesta_por_fuera = models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[MinValueValidator(0)])
