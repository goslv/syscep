/* listaEgresos.js — ITS CEP */
document.addEventListener('DOMContentLoaded', function () {

    const form           = document.getElementById('le-form-filtros');
    const searchInput    = document.getElementById('le-input-search');
    const btnToggle      = document.getElementById('le-btn-toggle-filters');
    const filtersPanel   = document.getElementById('le-filters-panel');
    const autoSubmitFields = document.querySelectorAll('.le-auto-submit');

    if (!form) return;

    /* ── 1. Mostrar / ocultar panel de filtros ── */
    btnToggle?.addEventListener('click', () => {
        const isVisible = filtersPanel.style.display === 'block';
        filtersPanel.style.display = isVisible ? 'none' : 'block';
        btnToggle.classList.toggle('active', !isVisible);
    });

    /* ── 2. Auto-submit para selects y fechas ── */
    autoSubmitFields.forEach(field => {
        field.addEventListener('change', () => form.submit());
    });

    /* ── 3. Auto-submit para la búsqueda (debounce 600ms) ── */
    if (searchInput) {
        let timeout = null;

        searchInput.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                if (searchInput.value.length > 2 || searchInput.value.length === 0) {
                    form.submit();
                }
            }, 600);
        });

        /* Mantener foco al final del input tras recarga */
        if (searchInput.value.length > 0) {
            searchInput.focus();
            searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
        }
    }
});