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
        if (fabContainer && fabMain) {
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
        }

        /* ── Carousel swipe con dots y swipe indicator ─────── */
        function initCarousels() {
            if (window.innerWidth > 768) return;

            document.querySelectorAll('.status-grid').forEach(function (grid) {
                const items = grid.querySelectorAll('.status-item');
                if (items.length < 2) return;
                if (grid.dataset.carouselInit) return;
                grid.dataset.carouselInit = '1';

                let indicatorHidden = false;
                function hideIndicator() {
                    if (indicatorHidden) return;
                    indicatorHidden = true;
                    indicator.classList.add('hidden');
                    setTimeout(function () {
                        if (indicator.parentNode) indicator.remove();
                    }, 500);
                }

                grid.addEventListener('scroll', hideIndicator, { passive: true, once: true });
                setTimeout(hideIndicator, 3000);

                /* Dots */
                const dotsContainer = document.createElement('div');
                dotsContainer.className = 'carousel-dots';

                items.forEach(function (_, i) {
                    const dot = document.createElement('button');
                    dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
                    dot.setAttribute('aria-label', 'Ir a tarjeta ' + (i + 1));
                    dot.addEventListener('click', function () {
                        items[i].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                    });
                    dotsContainer.appendChild(dot);
                });

                grid.parentNode.insertBefore(dotsContainer, grid.nextSibling);

                const dots = dotsContainer.querySelectorAll('.carousel-dot');

                function updateActiveDot() {
                    const gridRect   = grid.getBoundingClientRect();
                    const gridCenter = gridRect.left + gridRect.width / 2;
                    let closestIndex = 0;
                    let closestDist  = Infinity;
                    items.forEach(function (item, i) {
                        const rect   = item.getBoundingClientRect();
                        const center = rect.left + rect.width / 2;
                        const dist   = Math.abs(center - gridCenter);
                        if (dist < closestDist) { closestDist = dist; closestIndex = i; }
                    });
                    dots.forEach(function (dot, i) {
                        dot.classList.toggle('active', i === closestIndex);
                    });
                }

                grid.addEventListener('scroll', updateActiveDot, { passive: true });
                updateActiveDot();
            });
        }

        initCarousels();
    });

})();