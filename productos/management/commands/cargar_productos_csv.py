import csv
import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from productos.models import Producto

class Command(BaseCommand):
    help = 'Importa productos desde un archivo CSV'

    def handle(self, *args, **options):
        csv_file_path = os.path.join(settings.BASE_DIR, 'static', 'csv', 'productos.csv')

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f"Archivo no encontrado en: {csv_file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Importando productos desde {csv_file_path}..."))

        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)

                count = 0
                for row in reader:
                    producto, created = Producto.objects.get_or_create(
                        nombre=row['titulo'],
                        defaults={
                            'precio': Decimal(row['precio']),
                            'enlace_img': row['enlace']
                        }
                    )
                    
                    if created:
                        count += 1
                        self.stdout.write(self.style.SUCCESS(f"· Creado: {producto.nombre}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"· Ya existe (omitido): {producto.nombre}"))

            self.stdout.write(self.style.SUCCESS(f"\n¡Importación completada! Se crearon {count} nuevos productos."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ha ocurrido un error: {e}"))