// Validación adicional en el cliente
document.getElementById('materiaForm').addEventListener('submit', function(e) {
    const nombre = document.querySelector('input[name="nombre"]');
    const orden = document.querySelector('input[name="orden"]');

    if (!nombre.value.trim()) {
        e.preventDefault();
        alert('Por favor ingresa el nombre de la materia');
        nombre.focus();
        return false;
    }

    if (!orden.value || parseInt(orden.value) < 1) {
        e.preventDefault();
        alert('El orden debe ser un número mayor a 0');
        orden.focus();
        return false;
    }
});