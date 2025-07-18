from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess

class Command(BaseCommand):
    help = 'Exporta la base de datos MySQL a un archivo .sql'

    def handle(self, *args, **kwargs):
        db_settings = settings.DATABASES['default']
        user = db_settings['USER']
        password = db_settings['PASSWORD']
        host = db_settings['HOST']
        database = db_settings['NAME']
        output_file = 'exported_db.sql'
        command = [
            'mysqldump',
            f'-u{user}',
            f'-p{password}',
            f'-h{host}',
            database,
            '--result-file', output_file
        ]
        
        try:
            subprocess.run(command, check=True)
            self.stdout.write(self.style.SUCCESS(f'Base de datos exportada a {output_file}'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Error al exportar la base de datos: {e}'))
