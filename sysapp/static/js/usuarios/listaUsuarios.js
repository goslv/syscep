
// Función de búsqueda mejorada
document.getElementById('searchInput')?.addEventListener('keyup', function() {
    const searchValue = this.value.toLowerCase().trim();
    const tableRows = document.querySelectorAll('#userTableBody tr');
    let visibleCount = 0;

    tableRows.forEach(row => {
        if (row.querySelector('td[colspan]')) return; // Ignorar fila de empty state

        const text = row.textContent.toLowerCase();
        const isVisible = text.includes(searchValue);
        row.style.display = isVisible ? '' : 'none';

        if (isVisible) visibleCount++;
    });

    // Actualizar contador de resultados visibles
    const countElement = document.querySelector('.lu-table-count');
    if (countElement) {
        const total = tableRows.length - (document.querySelector('td[colspan]') ? 1 : 0);
        countElement.innerHTML = `<i class="bi bi-people"></i> ${visibleCount} de ${total} usuario${total !== 1 ? 's' : ''}`;
    }
});

// Inicializar animaciones
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.lu-stat').forEach((stat, index) => {
        stat.style.animationDelay = `${index * 0.05}s`;
    });
});
