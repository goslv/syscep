document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('lp-form-filtros');
    const searchInput = document.getElementById('input-search');
    const btnToggle = document.getElementById('btn-toggle-filters');
    const filtersPanel = document.getElementById('filters-panel');
    const autoSubmitFields = document.querySelectorAll('.auto-submit');

    // 1. Mostrar/Ocultar panel de filtros
    btnToggle.addEventListener('click', () => {
        const isVisible = filtersPanel.style.display === 'block';
        filtersPanel.style.display = isVisible ? 'none' : 'block';
        btnToggle.classList.toggle('active', !isVisible);
    });

    // 2. Auto-submit para select y fechas
    autoSubmitFields.forEach(field => {
        field.addEventListener('change', () => {
            form.submit();
        });
    });

    // 3. Auto-submit para búsqueda (con "debounce" para no saturar al servidor)
    let timeout = null;
    searchInput.addEventListener('input', () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            if (searchInput.value.length > 2 || searchInput.value.length === 0) {
                form.submit();
            }
        }, 600);
    });

    // Mantener el foco al final del input si se recarga por búsqueda
    if (searchInput.value.length > 0) {
        searchInput.focus();
        searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
    }
});