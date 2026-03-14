/* informeCaja.js — ITS CEP */
(function () {
    'use strict';

    /* ── toggleAll ────────────────────────────────────────── */
    window.toggleAll = function (className, checked) {
        document.querySelectorAll('.' + className).forEach(cb => cb.checked = checked);
    };

    /* ── setSortRecibo ────────────────────────────────────── */
    window.setSortRecibo = function (direction) {
        const url = new URL(window.location.href);
        if (url.searchParams.get('sort_recibo') === direction) {
            url.searchParams.delete('sort_recibo');
        } else {
            url.searchParams.set('sort_recibo', direction);
        }
        window.location.href = url.toString();
    };

    /* ── prepararYImprimir ────────────────────────────────── */
    window.prepararYImprimir = function () {
        const soloSeleccionados = document.getElementById('checkSoloSeleccionados').checked;
        const incIngresos       = document.getElementById('checkIngresos').checked;
        const incEgresos        = document.getElementById('checkEgresos').checked;

        const ingresosSection = document.querySelector('.lc-card:has(i.bi-arrow-up-circle-fill)');
        const egresosSection  = document.querySelector('.lc-card:has(i.bi-arrow-down-circle-fill)');

        document.querySelectorAll('tr').forEach(tr => tr.classList.remove('no-print'));

        if (ingresosSection) {
            if (!incIngresos) {
                ingresosSection.classList.add('no-print');
            } else {
                ingresosSection.classList.remove('no-print');
                if (soloSeleccionados) {
                    document.querySelectorAll('.ingreso-row').forEach(row => {
                        const cb = row.querySelector('.ingreso-check');
                        if (cb && !cb.checked) row.classList.add('no-print');
                    });
                }
            }
        }

        if (egresosSection) {
            if (!incEgresos) {
                egresosSection.classList.add('no-print');
            } else {
                egresosSection.classList.remove('no-print');
                if (soloSeleccionados) {
                    document.querySelectorAll('.egreso-row').forEach(row => {
                        const cb = row.querySelector('.egreso-check');
                        if (cb && !cb.checked) row.classList.add('no-print');
                    });
                }
            }
        }

        const modalEl = document.getElementById('modalImpresion');
        const modal   = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();

        setTimeout(() => window.print(), 300);
    };

    /* ── Modal de depósitos ───────────────────────────────── */
    function buildDepositosModal() {
        /* Recopilar datos de filas con data-metodo=DEPOSITO o MIXTO */
        const cuentas = new Map(); /* clave: nombre cuenta, valor: { total, items[] } */

        document.querySelectorAll('.ingreso-row[data-metodo]').forEach(row => {
            const metodo = row.dataset.metodo;
            if (metodo !== 'DEPOSITO' && metodo !== 'TRANSFERENCIA' && metodo !== 'MIXTO') return;

            const cuenta = row.dataset.cuenta  || 'Sin especificar';
            const dep    = parseFloat(row.dataset.dep) || 0;
            if (dep <= 0) return;

            const fecha    = row.dataset.fecha   || '—';
            const alumno   = row.dataset.alumno  || '—';
            const recibo   = row.dataset.recibo  || '';
            const url      = row.dataset.url     || null;
            const sinCuenta = cuenta === 'Sin especificar';

            if (!cuentas.has(cuenta)) cuentas.set(cuenta, { total: 0, items: [] });
            const entry = cuentas.get(cuenta);
            entry.total += dep;
            entry.items.push({ fecha, alumno, recibo, dep, url, sinCuenta });
        });

        const body = document.getElementById('modalDepositosBody');
        if (!body) return;

        if (cuentas.size === 0) {
            body.innerHTML = `
                <div class="lcd-empty">
                    <i class="bi bi-bank2"></i>
                    <p>No hay depósitos registrados en este período.</p>
                </div>`;
            return;
        }

        /* Total general */
        let totalGeneral = 0;
        cuentas.forEach(v => totalGeneral += v.total);

        let html = `
            <div class="lcd-total-banner">
                <span class="lcd-total-label"><i class="bi bi-bank2"></i> Total depositado</span>
                <span class="lcd-total-value">Gs. ${totalGeneral.toLocaleString('es-PY')}</span>
            </div>`;

        cuentas.forEach((data, cuenta) => {
            const pct       = Math.round((data.total / totalGeneral) * 100);
            const sinCuenta = data.items.some(i => i.sinCuenta);

            html += `
                <div class="lcd-cuenta-block">
                    <div class="lcd-cuenta-header">
                        <div class="lcd-cuenta-info">
                            <span class="lcd-cuenta-icon"><i class="bi bi-building-fill"></i></span>
                            <div>
                                <div class="lcd-cuenta-name">${cuenta}</div>
                                <div class="lcd-cuenta-count">${data.items.length} transacción${data.items.length !== 1 ? 'es' : ''}</div>
                            </div>
                        </div>
                        <div class="lcd-cuenta-right">
                            <div class="lcd-cuenta-total">Gs. ${data.total.toLocaleString('es-PY')}</div>
                            <div class="lcd-cuenta-pct">${pct}% del total</div>
                        </div>
                    </div>
                    <div class="lcd-bar-wrap">
                        <div class="lcd-bar-fill" style="width:${pct}%"></div>
                    </div>
                    <div class="lcd-items">
                        ${data.items.map(it => {
                const reciboHtml = it.recibo
                    ? `<span><i class="bi bi-receipt"></i> ${it.recibo}</span>`
                    : `<span style="opacity:.4">Sin recibo</span>`;

                const sinBancoTag = it.sinCuenta
                    ? `<span class="lcd-item-warn" title="Este pago no tiene cuenta bancaria registrada">
                                       <i class="bi bi-exclamation-triangle-fill"></i> Sin banco
                                   </span>`
                    : '';

                const inner = `
                                <span class="lcd-item-fecha">${it.fecha}</span>
                                <span class="lcd-item-alumno">${it.alumno}</span>
                                <span class="lcd-item-recibo">${reciboHtml}</span>
                                <div class="lcd-item-right">
                                    ${sinBancoTag}
                                    <span class="lcd-item-monto">Gs. ${it.dep.toLocaleString('es-PY')}</span>
                                    ${it.url ? `<span class="lcd-item-arrow"><i class="bi bi-arrow-right"></i></span>` : ''}
                                </div>`;

                return it.url
                    ? `<a href="${it.url}" class="lcd-item lcd-item-link" title="Ver detalle del pago">${inner}</a>`
                    : `<div class="lcd-item">${inner}</div>`;
            }).join('')}
                    </div>
                </div>`;
        });

        body.innerHTML = html;
    }

    /* ── Init ─────────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', () => {
        /* Click en stat-card violet → abrir modal depósitos */
        const statViolet = document.querySelector('.lc-stat-card.violet');
        if (statViolet) {
            statViolet.style.cursor = 'pointer';
            statViolet.addEventListener('click', () => {
                buildDepositosModal();
                const modalEl = document.getElementById('modalDepositos');
                if (modalEl) new bootstrap.Modal(modalEl).show();
            });

            /* Hint visual */
            const sub = statViolet.querySelector('.lc-stat-sub');
            if (sub) {
                sub.innerHTML = '<i class="bi bi-zoom-in"></i> Ver detalle por cuenta';
            }
        }
    });

})();