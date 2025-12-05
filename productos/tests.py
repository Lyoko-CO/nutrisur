from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.management import call_command
from decimal import Decimal
from unittest.mock import patch, mock_open
from io import StringIO
from .models import Producto
import os
import builtins

class ProductoModelTests(TestCase):
    """
    Tests enfocados en la integridad de los datos y validaciones del modelo Producto.
    """

    def test_creacion_producto_exitoso(self):
        """Caso Positivo: Crear un producto con todos los datos correctos."""
        prod = Producto.objects.create(
            nombre="Batido Premium",
            descripcion="Sabor chocolate rico en proteínas",
            precio=Decimal('45.50'),
            enlace_img="http://ejemplo.com/foto.jpg"
        )
        self.assertEqual(prod.nombre, "Batido Premium")
        self.assertEqual(prod.precio, Decimal('45.50'))
        self.assertEqual(str(prod), "Batido Premium")

    def test_campos_opcionales_vacios(self):
        """Caso Positivo: Crear producto sin descripción ni imagen (debe permitirse)."""
        prod = Producto.objects.create(
            nombre="Producto Simple",
            precio=10.00
        )
        self.assertIsNone(prod.enlace_img)
        self.assertTrue(prod.descripcion is None or prod.descripcion == "")

    def test_validacion_precio_negativo(self):
        prod = Producto.objects.create(nombre="Test Negativo", precio=-5.00)
        self.assertEqual(prod.precio, -5.00)

    def test_validacion_nombre_largo(self):
        """Caso Negativo: El nombre no debe exceder los 100 caracteres."""
        nombre_muy_largo = "A" * 101
        prod = Producto(nombre=nombre_muy_largo, precio=10)
        
        with self.assertRaises(ValidationError):
            prod.full_clean()

    def test_validacion_precio_null(self):
        """Caso Negativo: El precio es obligatorio."""
        prod = Producto(nombre="Producto Gratis")
        with self.assertRaises(ValidationError):
            prod.full_clean()


class CargaCSVCommandTests(TestCase):
    """
    Tests para el comando 'cargar_productos_csv'.
    """

    def setUp(self):
        self.out = StringIO()
        self.original_open = builtins.open

    def open_side_effect(self, csv_data):
        """
        Crea una función que simula open(). 
        Si el archivo es 'productos.csv', devuelve el mock con nuestros datos.
        Si es cualquier otro archivo, usa el open real.
        """
        def _side_effect(file, mode='r', *args, **kwargs):
            filename = str(file)
            
            if 'productos.csv' in filename:
                mock_file = mock_open(read_data=csv_data).return_value
                return mock_file
            
            return self.original_open(file, mode, *args, **kwargs)
            
        return _side_effect

    @patch('os.path.exists')
    def test_comando_archivo_no_existe(self, mock_exists):
        """Caso Negativo: El archivo CSV no se encuentra."""
        mock_exists.return_value = False
        
        call_command('cargar_productos_csv', stdout=self.out)
        
        salida = self.out.getvalue()
        self.assertIn("Archivo no encontrado", salida)
        self.assertEqual(Producto.objects.count(), 0)

    @patch('os.path.exists')
    def test_comando_importacion_correcta(self, mock_exists):
        """Caso Positivo: Importación exitosa de un CSV válido."""
        mock_exists.return_value = True
        csv_content = "titulo,precio,enlace\nProducto A,10.50,http://a.jpg\nProducto B,20.00,http://b.jpg"
        
        with patch('builtins.open', side_effect=self.open_side_effect(csv_content)):
            call_command('cargar_productos_csv', stdout=self.out)
        
        salida = self.out.getvalue()
        self.assertIn("Importación completada", salida)
        self.assertIn("Creado: Producto A", salida)
        self.assertEqual(Producto.objects.count(), 2)

    @patch('os.path.exists')
    def test_comando_evita_duplicados(self, mock_exists):
        """Caso Lógica: No debe duplicar si el nombre ya existe."""
        mock_exists.return_value = True
        csv_content = "titulo,precio,enlace\nProducto A,10.50,http://a.jpg\nProducto A,15.00,http://otra.jpg"
        
        with patch('builtins.open', side_effect=self.open_side_effect(csv_content)):
            call_command('cargar_productos_csv', stdout=self.out)
        
        salida = self.out.getvalue()
        self.assertIn("Creado: Producto A", salida)
        self.assertIn("Ya existe (omitido): Producto A", salida)
        self.assertEqual(Producto.objects.count(), 1)

    @patch('os.path.exists')
    def test_comando_precio_invalido(self, mock_exists):
        """Caso Negativo: El CSV tiene texto donde debería ir un número."""
        mock_exists.return_value = True
        csv_content = "titulo,precio,enlace\nProducto Malo,GRATIS,http://a.jpg"
        
        with patch('builtins.open', side_effect=self.open_side_effect(csv_content)):
            call_command('cargar_productos_csv', stdout=self.out)
        
        salida = self.out.getvalue()
        self.assertIn("Ha ocurrido un error", salida)
        self.assertEqual(Producto.objects.count(), 0)

    @patch('os.path.exists')
    def test_comando_columnas_incorrectas(self, mock_exists):
        """Caso Negativo: El CSV no tiene las columnas esperadas."""
        mock_exists.return_value = True
        csv_content = "columna_inventada,otra\nDatos,MasDatos"
        
        with patch('builtins.open', side_effect=self.open_side_effect(csv_content)):
            call_command('cargar_productos_csv', stdout=self.out)
        
        salida = self.out.getvalue()
        self.assertIn("Ha ocurrido un error", salida)