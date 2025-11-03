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

### 2. Producto (Product)

Representa los artículos de la tienda Herbalife que los usuarios pueden comprar.

* **Atributos Principales:**
    * `id_producto` (Clave primaria)
    * `nombre`
    * `descripcion`
    * `precio`
    * `imagen_url`

### 3. Pedido (Order)

Este componente centraliza la transacción de compra. Debe diseñarse para aceptar pedidos tanto de usuarios registrados como de "invitados" (sin *login*).

* **Atributos Principales:**
    * `id_pedido` (Clave primaria)
    * `fecha_creacion`
    * `estado` (Valores: "Pendiente", "Realizado")
    * `coste_total`
* **Atributos de Invitado (para checkout sin login):**
    * `nombre_cliente`
    * `telefono_cliente`
    * `email_cliente`
* **Relaciones:**
    * `id_usuario` (FK a `Usuario`, *opcional/nulable* para permitir invitados).

### 4. ItemPedido (Order Item)

Componente asociativo que vincula un `Pedido` específico con un `Producto` específico y almacena la cantidad deseada.

* **Atributos Principales:**
    * `cantidad`
* **Relaciones:**
    * `id_pedido` (FK a `Pedido`)
    * `id_producto` (FK a `Producto`)