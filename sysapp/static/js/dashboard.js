(function () {
    'use strict';

    if (document.body.dataset.dashboardInit) return;
    document.body.dataset.dashboardInit = '1';

    document.addEventListener('DOMContentLoaded', function () {

        /* ── Animación de contadores ───────────────────────── */
        document.querySelectorAll('.stat-content h2').forEach(function (el) {
            const finalValue = parseInt(el.textContent) || 0;
            if (finalValue === 0) return;

            let currentValue = 0;
            const increment = Math.ceil(finalValue / 50);
            const stepTime  = 1000 / (finalValue / increment);
            el.textContent  = '0';

            const timer = setInterval(function () {
                currentValue += increment;
                if (currentValue >= finalValue) {
                    el.textContent = finalValue.toLocaleString('es-PY');
                    clearInterval(timer);
                } else {
                    el.textContent = currentValue.toLocaleString('es-PY');
                }
            }, stepTime);
        });

        /* ── Animación de barras de porcentaje ─────────────── */
        setTimeout(function () {
            document.querySelectorAll('.percentage-fill').forEach(function (fill) {
                const width = fill.style.width;
                fill.style.width = '0%';
                setTimeout(function () { fill.style.width = width; }, 100);
            });
        }, 500);

        /* ── Hover en filas de la tabla ────────────────────── */
        document.querySelectorAll('.table-modern tbody tr').forEach(function (row) {
            row.addEventListener('mouseenter', function () { this.style.transform = 'scale(1.01)'; });
            row.addEventListener('mouseleave', function () { this.style.transform = 'scale(1)'; });
        });

        /* ── FAB — Menú de acción rápida ───────────────────── */
        const fabContainer = document.getElementById('fabContainer');
        const fabMain      = document.getElementById('fabMain');
        if (!fabContainer || !fabMain) return;

        const overlay = document.createElement('div');
        overlay.className = 'fab-overlay';
        document.body.appendChild(overlay);

        function openFab()  { fabContainer.classList.add('active');    overlay.classList.add('show'); }
        function closeFab() { fabContainer.classList.remove('active'); overlay.classList.remove('show'); }
        function toggleFab() {
            fabContainer.classList.contains('active') ? closeFab() : openFab();
        }

        fabMain.addEventListener('click',   function (e) { e.stopPropagation(); toggleFab(); });
        overlay.addEventListener('click',   closeFab);
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeFab(); });
        document.querySelectorAll('.fab-item').forEach(function (item) {
            item.addEventListener('click', closeFab);
        });
    });

})();