from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone

# Create your models here.
class CustomUserManager(BaseUserManager):
    
    def create_user(self, email, nombre, telefono, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio para crear un usuario.")
        if not nombre:
            raise ValueError("El nombre es obligatorio para crear un usuario.")
        
        
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, telefono=telefono, **extra_fields)
        user.set_password(password)  # Cifra la contraseña
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nombre, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
            
        user = self.model(email=self.normalize_email(email), nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    
    is_staff = models.BooleanField(default=False)   
    is_active = models.BooleanField(default=True)   
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD= 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'     
        
    def __str__(self):
        return f"{self.nombre}, ({self.email})"   