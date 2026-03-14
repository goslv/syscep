// Función para filtrar por estado (desde las cards)
function applyFilter(estado) {
    window.location.href = window.location.pathname + '?estado=' + estado;
}

// Función de búsqueda en tiempo real
document.getElementById('searchInput')?.addEventListener('keyup', function() {
    const searchValue = this.value.toLowerCase().trim();
    const tableRows = document.querySelectorAll('#alumnoTableBody tr');
    let visibleCount = 0;

    tableRows.forEach(row => {
        if (row.id === 'emptyRow') return;

        const text = row.textContent.toLowerCase();
        const isVisible = text.includes(searchValue);
        row.style.display = isVisible ? '' : 'none';

        if (isVisible) visibleCount++;
    });

    const countElement = document.getElementById('visibleCount');
    if (countElement) {
        countElement.textContent = visibleCount;
    }

    const emptyRow = document.getElementById('emptyRow');
    const hasVisibleRows = visibleCount > 0;

    if (!hasVisibleRows && !emptyRow) {
        const tbody = document.getElementById('alumnoTableBody');
        const noResultsRow = document.createElement('tr');
        noResultsRow.id = 'noResultsRow';
        noResultsRow.innerHTML = `
                <td colspan="5">
                    <div class="la-empty">
                        <div class="la-empty-illustration">
                            <i class="bi bi-search"></i>
                        </div>
                        <h3>No se encontraron resultados</h3>
                        <p>No hay alumnos que coincidan con "${searchValue}"</p>
                    </div>
                </td>
            `;
        tbody.appendChild(noResultsRow);
    } else if (hasVisibleRows) {
        const noResultsRow = document.getElementById('noResultsRow');
        if (noResultsRow) noResultsRow.remove();
    }
});

// Inicializar contador
document.addEventListener('DOMContentLoaded', function() {
    const totalRows = document.querySelectorAll('#alumnoTableBody tr:not(#emptyRow)').length;
    document.getElementById('visibleCount').textContent = totalRows;
});