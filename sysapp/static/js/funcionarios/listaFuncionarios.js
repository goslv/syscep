// Función para aplicar filtro desde las cards
function applyFilter(filterName, filterValue) {
    const url = new URL(window.location.href);
    url.searchParams.set(filterName, filterValue);
    window.location.href = url.toString();
}

// Función para colapsar/expandir filtros
function toggleFilters() {
    document.getElementById('filtersCard').classList.toggle('collapsed');
}

// Función de búsqueda en tiempo real
document.getElementById('searchInput')?.addEventListener('keyup', function() {
    const searchValue = this.value.toLowerCase().trim();
    const tableRows = document.querySelectorAll('#funcionarioTableBody tr');
    let visibleCount = 0;

    tableRows.forEach(row => {
        // Ignorar la fila de empty state si existe
        if (row.id === 'emptyRow') return;

        const text = row.textContent.toLowerCase();
        const isVisible = text.includes(searchValue);
        row.style.display = isVisible ? '' : 'none';

        if (isVisible) visibleCount++;
    });

    // Actualizar contador de resultados visibles
    const countElement = document.getElementById('visibleCount');
    if (countElement) {
        countElement.textContent = visibleCount;
    }

    // Mostrar mensaje si no hay resultados
    const emptyRow = document.getElementById('emptyRow');
    const hasVisibleRows = visibleCount > 0;

    if (!hasVisibleRows && !emptyRow) {
        // Crear fila de "no resultados" si no existe
        const tbody = document.getElementById('funcionarioTableBody');
        const noResultsRow = document.createElement('tr');
        noResultsRow.id = 'noResultsRow';
        noResultsRow.innerHTML = `
                <td colspan="8">
                    <div class="lf-empty">
                        <div class="lf-empty-illustration">
                            <i class="bi bi-search"></i>
                        </div>
                        <h3>No se encontraron resultados</h3>
                        <p>No hay funcionarios que coincidan con "${searchValue}"</p>
                    </div>
                </td>
            `;
        tbody.appendChild(noResultsRow);
    } else if (hasVisibleRows) {
        // Eliminar fila de "no resultados" si existe
        const noResultsRow = document.getElementById('noResultsRow');
        if (noResultsRow) noResultsRow.remove();
    }
});

// Inicializar contador y estado de filtros
document.addEventListener('DOMContentLoaded', function() {
    const totalRows = document.querySelectorAll('#funcionarioTableBody tr:not(#emptyRow)').length;
    const countElement = document.getElementById('visibleCount');
    if (countElement) {
        countElement.textContent = totalRows;
    }

    // Colapsar filtros si no hay parámetros activos
    const params = new URLSearchParams(window.location.search);
    if (!params.get('cargo') && !params.get('sede') && !params.get('activo')) {
        document.getElementById('filtersCard')?.classList.add('collapsed');
    }
});