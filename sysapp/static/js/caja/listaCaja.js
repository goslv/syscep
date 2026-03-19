// ─── Estado de cada tabla (asc por defecto) ────────────────
const sortState = { ingresos: 'asc', egresos: 'asc' };

// Extrae el número entero de un string de recibo/comprobante
function extraerNumero(val) {
    if (!val) return null;
    const solo = val.replace(/\D/g, '');
    return solo ? parseInt(solo, 10) : null;
}

// ─── Toggle principal ──────────────────────────────────────
function toggleSort(tab) {
    // Invertir estado
    sortState[tab] = sortState[tab] === 'asc' ? 'desc' : 'asc';
    const isAsc = sortState[tab] === 'asc';

    // Reordenar filas en el DOM
    const tbody = document.getElementById('tbody-' + tab);
    const rows  = [...tbody.querySelectorAll('tr[data-num]')];

    rows.sort((a, b) => {
        const nA = extraerNumero(a.dataset.num);
        const nB = extraerNumero(b.dataset.num);
        // Filas sin número siempre al final
        if (nA === null && nB === null) return 0;
        if (nA === null) return 1;
        if (nB === null) return -1;
        return isAsc ? nA - nB : nB - nA;
    });
    rows.forEach(r => tbody.appendChild(r));

    // ─── Actualizar botón ──────────────────────────────────
    const btn   = document.getElementById('btn-sort-' + tab);
    const icon  = btn.querySelector('.sort-icon');
    const label = document.getElementById('label-sort-' + tab);
    const th    = document.getElementById('th-' + tab);
    const foot  = document.getElementById('footer-' + tab);
    const etiq  = tab === 'ingresos' ? 'Recibo' : 'Comp.';

    if (isAsc) {
        // ── ASC ──
        btn.className         = 'btn-sort order-asc';
        icon.className        = 'bi bi-sort-numeric-down sort-icon';
        label.textContent     = `${etiq}: ASC`;
        th.className          = 'th-recibo asc';
        th.querySelector('.th-sort-arrow').className = 'bi bi-arrow-up th-sort-arrow';
        if (foot) foot.innerHTML = `<i class="bi bi-sort-numeric-down me-1"></i>N° ${etiq}: ASC`;
    } else {
        // ── DESC ──
        btn.className         = 'btn-sort order-desc';
        icon.className        = 'bi bi-sort-numeric-up-alt sort-icon';
        label.textContent     = `${etiq}: DESC`;
        th.className          = 'th-recibo desc';
        th.querySelector('.th-sort-arrow').className = 'bi bi-arrow-down th-sort-arrow';
        if (foot) foot.innerHTML = `<i class="bi bi-sort-numeric-up-alt me-1"></i>N° ${etiq}: DESC`;
    }
}

// ─── Tabs ──────────────────────────────────────────────────
document.querySelectorAll('.lc-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        document.querySelectorAll('.lc-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.lc-tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('tab-' + target).classList.add('active');
    });
});

// ─── Orden inicial ASC al cargar ──────────────────────────
// Hacemos un ciclo desc→asc para que la lógica de sort se ejecute
document.addEventListener('DOMContentLoaded', () => {
    sortState.ingresos = 'desc'; toggleSort('ingresos');
    sortState.egresos  = 'desc'; toggleSort('egresos');
});
