document.addEventListener("DOMContentLoaded", function() {
    // 1. Buscamos el formulario de la lista (la tabla)
    const form = document.getElementById("changelist-form");
    
    // 2. Buscamos el botón de guardar (Jazzmin lo suele poner abajo o arriba)
    // Buscamos cualquier input que sirva para guardar
    const saveButtons = document.querySelectorAll('input[name="_save"]');

    if (form && saveButtons.length > 0) {
        
        // 3. Escuchamos CUALQUIER cambio dentro de la tabla
        form.addEventListener("change", function() {
            
            saveButtons.forEach(btn => {
                // Cambiamos el color a ROJO (Peligro/Atención)
                // Quitamos las clases verdes/azules por defecto de Jazzmin
                btn.classList.remove("btn-success", "btn-primary", "btn-info");
                btn.classList.add("btn-danger"); // Rojo intenso
                
                // Cambiamos el texto para que sea evidente
                btn.value = "⚠️ GUARDAR CAMBIOS PENDIENTES";
                
                // Opcional: Añadir una animación de parpadeo suave con CSS
                btn.style.transition = "all 0.3s ease";
                btn.style.transform = "scale(1)";
                btn.style.boxShadow = "0 0 10px rgba(220, 53, 69, 0.5)";
            });

        });
    }
});