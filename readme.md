#  NUTRISUR 🏆

![Badge Version](https://img.shields.io/badge/VERSIÓN-1.0.0-blue)  
<img src="static\images\lyoko-logo.jpg" alt="Logo Lyoko" width="20%">  

**Nutrisur** es una aplicación web diseñada para [Fernando Escalona](https://www.instagram.com/fernandoescalona78/?hl=es), CEO de Natursur, con el objetivo aunar sus dos líneas de negocio relacionadas con la salud: la compra de productos alimenticios y la gestión de citas de servicios como masajes o asesoramiento nutricional.

🔗 **Aplicación desplegada:** [Nutrisur](https://nutrisur.onrender.com)

## 🛠️ Tecnologías Usadas

La aplicación fue desarrollada utilizando el *framework full-stack* Django, utilizando el lenguaje Python.

## 📋 Prerrequisitos

Antes de lanzar la aplicación de manera local, asegúrate de tener instalado [Python](https://www.python.org/downloads/release/python-31212/) (versión 3.12).

## 🚀 Instalación y configuración

Sigue estos pasos para levantar el proyecto en tu entorno local en Windows:

1. **Crea una carpeta para alojar el proyecto y el entorno virtual de Python.**
    ```bash
    mkdir <nombre_carpeta>
    ```

2. **Dentro de la carpeta, crea un entorno virtual de python.**
    ```bash
    cd <nombre_carpeta>
    python -m venv .venv
    ```

3. **En la misma carpeta creada, clona el repositorio.**
    ```bash
    git clone https://github.com/Lyoko-CO/nutrisur
    ```

4. **Entra a la carpeta raíz del proyecto e instala las dependencias.**
    ```bash
    cd nutrisur
    pip install -r requirements.txt
    ```

5.  **Configura las variables de entorno.**  
    Crea un archivo `.env` en la raíz del proyecto y añade la siguiente variable:
    ```env
    GEMINI_API_KEY=<api_secreta_de_gemini>
    EMAIL_HOST_USER=<usuario_correo>
    EMAIL_HOST_PASSWORD=<contraseña_correo>
    ```
    Nota: debes utilizar tu propia API de Gemini para utilizar el chatbot y tu propia cuenta de correo electrónico con la que enviar/recibir mensajes de confirmación.

6.  **Inicia el servidor de desarrollo.**
    ```bash
    python manage.py runserver
    ```

7.  **Abre la aplicación:**  
    Visita `http://127.0.0.1:8000` en tu navegador.



## ✋🏼🤚🏼 Equipo de Lyoko

* **Max Cameron Corti** - *Project Manager* - [[Enlace al perfil de GitHub](https://github.com/MaxCorti)]
* **Francisco Ayala Díaz** - *Desarrollador y tester* - [[Enlace al perfil de GitHub](https://github.com/CurroAyala)]
* **Nicolás Parrilla Geniz** - *Analista, desarrollador y tester* - [[Enlace al perfil de GitHub](https://github.com/Nicoparri)]
* **Javier Luque Ruiz** - *Desarrollador y tester* - [[Enlace al perfil de GitHub](https://github.com/Javierluqueruiz)]
