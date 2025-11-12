## Componentes del Sistema

Esta es la definición de los componentes del sistema, a partir de los cuales se crearán las entidades del back-end y las tablas de las bases de datos.

### 1. Usuario (User)

Este componente gestiona la identidad y autenticación de los usuarios registrados. Es fundamental para los requisitos de inicio de sesión y registro.

* **Atributos Principales:**
    * `id_usuario` (Clave primaria)
    * `nombre`
    * `email` (Usado para login)
    * `telefono`
    * `password` (Almacenada de forma segura, *hashed*)
    * `es_admin` (Booleano para identificar al "Cliente" administrador)

### 2. Pedido (Order)

Este componente gestiona la informacíon que intercambia el usuario con el chatbot. Debe diseñarse para aceptar pedidos tanto de usuarios registrados como de "invitados" (sin *login*).

* **Atributos Principales:**
    * `id_pedido` (Clave primaria)
    * `fecha`
    * `estado` (Valores: "Pendiente", "Realizado")
    * `coste_total`
    * `descripciónPedido`
* **Atributos de Invitado (para checkout sin login):**
    * `nombre_cliente`
    * `telefono_cliente`
    * `email_cliente`
* **Relaciones:**
    * `id_usuario` (FK a `Usuario`, *opcional/nulable* para permitir invitados).

### 3. Cita (Session)

Este componente gestiona las citas que los usuarios reservan a traves del chatbot. Incluye detalles como la fecha, hora y estado de la cita.
* **Atributos Principales:**
    * `id_cita` (Clave primaria)
    * `fecha`
    * `tipo`
    * `estado` (Valores: "Reservada", "Completada", "Cancelada")
    * **Atributos de Invitado (para checkout sin login):**
    * `nombre_cliente`
    * `telefono_cliente`
    * `email_cliente`
* **Relaciones:**
    * `id_usuario` (FK a `Usuario`, *opcional/nulable* para permitir invitados).