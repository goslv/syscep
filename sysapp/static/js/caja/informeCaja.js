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
            const titular = row.dataset.titular || '';
            const dep    = parseFloat(row.dataset.dep) || 0;
            if (dep <= 0) return;

            const fecha    = row.dataset.fecha   || '—';
            const alumno   = row.dataset.alumno  || '—';
            const recibo   = row.dataset.recibo  || '';
            const url      = row.dataset.url     || null;
            const sinCuenta = cuenta === 'Sin especificar';

            const fullCuenta = titular ? `${cuenta} — ${titular}` : cuenta;

            if (!cuentas.has(fullCuenta)) cuentas.set(fullCuenta, { total: 0, items: [] });
            const entry = cuentas.get(fullCuenta);
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

    /* ── Actualización de stat-cards por selección ────────── */
    const fmt = n => Math.abs(n).toLocaleString('es-PY');

    /* Valores originales — se guardan al cargar para poder restaurar */
    let origIngresos = 0, origEgresos = 0, origBalance = 0, origDeposito = 0;
    let origIngresosCount = '', origEgresosCount = '';

    function guardarOriginales() {
        /* Leer los valores numéricos de las filas, no del DOM, para evitar
           problemas de formato al restaurar */
        document.querySelectorAll('.ingreso-row').forEach(r => {
            origIngresos += parseFloat(r.dataset.importe || 0);
            origDeposito += parseFloat(r.dataset.dep     || 0);  /* solo dep */
        });
        document.querySelectorAll('.egreso-row').forEach(r => {
            origEgresos  += parseFloat(r.dataset.monto   || 0);
        });
        origBalance = origIngresos - origEgresos;

        const ci = document.querySelectorAll('.ingreso-row').length;
        const ce = document.querySelectorAll('.egreso-row').length;
        origIngresosCount = `${ci} registro${ci !== 1 ? 's' : ''}`;
        origEgresosCount  = `${ce} registro${ce !== 1 ? 's' : ''}`;
    }

    function updateStats() {
        const ingChecks = document.querySelectorAll('.ingreso-check:checked');
        const egChecks  = document.querySelectorAll('.egreso-check:checked');
        const haySeleccion = ingChecks.length > 0 || egChecks.length > 0;

        if (!haySeleccion) {
            /* Restaurar valores originales */
            setStatCard('ing', origIngresos, origIngresosCount, false);
            setStatCard('eg',  origEgresos,  origEgresosCount,  false);
            setStatCard('bal', origBalance,  '',                false);
            setStatDeposito(origDeposito, false);
            resetTfoot();
            updatePrintNotice(false, 0, 0);
            return;
        }

        /* Calcular totales de la selección */
        let selIngresos = 0, selEgresos = 0, selDeposito = 0;

        ingChecks.forEach(cb => {
            const row = cb.closest('.ingreso-row');
            selIngresos += parseFloat(row?.dataset.importe || 0);
            selDeposito += parseFloat(row?.dataset.dep     || 0);
        });
        egChecks.forEach(cb => {
            const row = cb.closest('.egreso-row');
            selEgresos  += parseFloat(row?.dataset.monto   || 0);
        });

        const selBalance = selIngresos - selEgresos;
        const labelI = `${ingChecks.length} seleccionado${ingChecks.length !== 1 ? 's' : ''}`;
        const labelE = `${egChecks.length} seleccionado${egChecks.length !== 1 ? 's' : ''}`;

        setStatCard('ing', selIngresos, labelI, true);
        setStatCard('eg',  selEgresos,  labelE, true);
        setStatCard('bal', selBalance,  '',      true);
        setStatDeposito(selDeposito, true);
        updateTfoot(selIngresos, selEgresos);
        updatePrintNotice(true, ingChecks.length, egChecks.length);
    }

    function setStatCard(tipo, valor, subtext, selMode) {
        const ids = {
            ing: { val: 'statIngresosVal', sub: 'statIngresosSub', lbl: 'statIngresosLabel', card: 'statCardIngresos', pkVal: 'pkIngresosVal', pkLbl: 'pkIngresosLabel' },
            eg:  { val: 'statEgresosVal',  sub: 'statEgresosSub',  lbl: 'statEgresosLabel',  card: 'statCardEgresos',  pkVal: 'pkEgresosVal',  pkLbl: 'pkEgresosLabel'  },
            bal: { val: 'statBalanceVal',   sub: 'statBalanceSub',  lbl: 'statBalanceLabel',  card: 'statCardBalance',  pkVal: 'pkBalanceVal',  pkLbl: 'pkBalanceLabel'  },
        };
        const m = ids[tipo]; if (!m) return;

        const valEl  = document.getElementById(m.val);
        const subEl  = document.getElementById(m.sub);
        const lblEl  = document.getElementById(m.lbl);
        const card   = document.getElementById(m.card);
        const pkVal  = document.getElementById(m.pkVal);
        const pkLbl  = document.getElementById(m.pkLbl);
        if (!valEl) return;

        const texto = fmt(valor);
        valEl.textContent = texto;

        /* Sincronizar print-kpi-strip */
        if (pkVal) pkVal.textContent = texto;

        const labelWeb = selMode
            ? (tipo === 'ing' ? 'Ingresos selec.' : tipo === 'eg' ? 'Egresos selec.' : 'Balance selec.')
            : (tipo === 'ing' ? 'Total Ingresos'  : tipo === 'eg' ? 'Total Egresos'  : 'Balance Neto');

        if (lblEl) lblEl.textContent = labelWeb;
        if (pkLbl) pkLbl.textContent = selMode
            ? (tipo === 'ing' ? 'Ingresos selec.' : tipo === 'eg' ? 'Egresos selec.' : 'Balance selec.')
            : (tipo === 'ing' ? 'Total Ingresos'  : tipo === 'eg' ? 'Total Egresos'  : 'Balance Neto');

        if (subEl && subtext !== '') {
            const icono = selMode ? 'check2-circle' : (tipo === 'ing' ? 'receipt' : tipo === 'eg' ? 'file-text' : 'arrow-left-right');
            subEl.innerHTML = `<i class="bi bi-${icono}"></i> ${subtext}`;
        }

        /* Balance: cambiar color de la card */
        if (tipo === 'bal' && card) {
            card.classList.remove('blue', 'green', 'red');
            card.classList.add(valor >= 0 ? 'blue' : 'red');
        }

        if (card) card.classList.toggle('lc-stat-sel-mode', selMode);
    }

    function setStatDeposito(valor, selMode) {
        const valEl = document.getElementById('statDepositoVal');
        const lblEl = document.getElementById('statDepositoLabel');
        const card  = document.getElementById('statCardDeposito');
        const pkVal = document.getElementById('pkDepositoVal');
        const pkLbl = document.getElementById('pkDepositoLabel');
        if (!valEl) return;
        const texto = fmt(valor);
        valEl.textContent = texto;
        if (pkVal) pkVal.textContent = texto;
        if (lblEl) lblEl.textContent = selMode ? 'Depósitos selec.' : 'Depósitos';
        if (pkLbl) pkLbl.textContent = selMode ? 'Depósitos selec.' : 'Depósito / Transferencia';
        if (card)  card.classList.toggle('lc-stat-sel-mode', selMode);
    }

    function updateTfoot(ingresos, egresos) {
        const tfI = document.getElementById('tfootIngresosVal');
        const tfE = document.getElementById('tfootEgresosVal');
        const tlI = document.getElementById('tfootIngresosLabel');
        const tlE = document.getElementById('tfootEgresosLabel');
        if (tfI) tfI.textContent = `Gs. ${fmt(ingresos)}`;
        if (tfE) tfE.textContent = `Gs. ${fmt(egresos)}`;
        if (tlI) tlI.textContent = 'SUBTOTAL SEL.';
        if (tlE) tlE.textContent = 'SUBTOTAL SEL.';
    }

    function resetTfoot() {
        const tfI = document.getElementById('tfootIngresosVal');
        const tfE = document.getElementById('tfootEgresosVal');
        const tlI = document.getElementById('tfootIngresosLabel');
        const tlE = document.getElementById('tfootEgresosLabel');
        if (tfI) tfI.textContent = `Gs. ${fmt(origIngresos)}`;
        if (tfE) tfE.textContent = `Gs. ${fmt(origEgresos)}`;
        if (tlI) tlI.textContent = 'SUBTOTAL';
        if (tlE) tlE.textContent = 'SUBTOTAL EGRESOS';
    }

    function updatePrintNotice(haySeleccion, countI, countE) {
        const notice   = document.getElementById('printSelNotice');
        const countEl  = document.getElementById('printSelCount');
        if (!notice) return;
        if (haySeleccion) {
            const partes = [];
            if (countI > 0) partes.push(`${countI} ingreso${countI !== 1 ? 's' : ''}`);
            if (countE > 0) partes.push(`${countE} egreso${countE !== 1 ? 's' : ''}`);
            if (countEl) countEl.textContent = partes.join(' y ');
            notice.style.display = 'block';
        } else {
            notice.style.display = 'none';
        }
    }

    function setupSeleccion() {
        guardarOriginales();

        /* Delegación: captura checkboxes individuales */
        document.addEventListener('change', e => {
            if (e.target.classList.contains('ingreso-check') ||
                e.target.classList.contains('egreso-check'))  updateStats();
        });

        /* "Seleccionar todos" */
        document.getElementById('selectAllIngresos')?.addEventListener('change', updateStats);
        document.getElementById('selectAllEgresos')?.addEventListener('change', updateStats);
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

            const sub = statViolet.querySelector('.lc-stat-sub');
            if (sub) sub.innerHTML = '<i class="bi bi-zoom-in"></i> Ver detalle por cuenta';
        }

        setupSeleccion();
    });

})();