/* formPagos.js — ITS CEP
   Requiere: carrerasData, cuentasBancarias y cuentaBancariaActual
   inyectados como variables globales desde el template Django.
*/
(function () {
    'use strict';

    /* ── Guard ──────────────────────────────────────────── */
    if (document.body.dataset.pfInit) return;
    document.body.dataset.pfInit = '1';

    /* ── Helpers ────────────────────────────────────────── */
    const $   = id => document.getElementById(id);
    const deb = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

    /* ── Datos externos (inyectados en el template) ──────── */
    /* Se esperan como vars globales: window.PF_CARRERAS, window.PF_CUENTAS */
    const carrerasData    = window.PF_CARRERAS   || [];
    let   cuentasBancarias = window.PF_CUENTAS   || [];
    const CM = new Map(carrerasData.map(c => [String(c.id), c]));

    /* ── Auto-advance ────────────────────────────────────── */
    function advanceTo(el) {
        if (!el) return;
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => el.focus(), 120);
    }

    function isVisible(el) {
        if (!el) return false;
        const s = window.getComputedStyle(el);
        return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetParent !== null && !el.disabled;
    }

    function getAllFocusable() {
        return Array.from(document.querySelectorAll(
            '#pagoForm input:not([type=hidden]):not([type=radio]):not([type=checkbox]),' +
            '#pagoForm select,' +
            '#pagoForm textarea,' +
            '#alumnoTrigger'
        )).filter(isVisible);
    }

    function getNextFocusable(currentEl) {
        const all = getAllFocusable();
        const idx = all.indexOf(currentEl);
        return idx < 0 ? null : (all[idx + 1] || null);
    }

    function setupEnterAdvance() {
        $('pagoForm')?.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter') return;
            if (e.target.tagName === 'TEXTAREA') return;
            if (e.target.type === 'submit') return;
            if (e.target.closest('.pf-alumno-dropdown')) return;
            e.preventDefault();
            if (e.target === $('alumnoTrigger')) { openAlumnoDropdown(); return; }
            const next = getNextFocusable(e.target);
            if (next) advanceTo(next);
        });

        $('id_fecha')?.addEventListener('change', () => {
            setTimeout(() => advanceTo($('alumnoTrigger')), 80);
        });
        $('id_sede')?.addEventListener('change', () => {
            setTimeout(() => advanceTo($('id_carrera')), 60);
        });
        $('id_carrera')?.addEventListener('change', () => {
            setTimeout(() => {
                const next = $('id_es_matricula')?.checked ? $('id_importe_total') : $('id_numero_cuota');
                if (isVisible(next)) advanceTo(next);
            }, 90);
        });
        document.querySelectorAll('input[name="metodo_pago"]').forEach(r => {
            r.addEventListener('change', () => {
                setTimeout(() => { if (isVisible($('id_concepto'))) advanceTo($('id_concepto')); }, 400);
            });
        });
    }

    /* ── Importes ────────────────────────────────────────── */
    function calcImporte() {
        if ($('id_es_matricula')?.checked) return;
        const mu   = parseFloat($('id_monto_unitario')?.value) || 0;
        const cant = parseInt($('id_cantidad_cuotas')?.value || '1', 10) || 1;
        if (mu > 0) { $('id_importe_total').value = mu * cant; updateSplitCheck(); }
    }

    function applyCarrera(id) {
        const c = CM.get(String(id)); if (!c) return;
        const esM = $('id_es_matricula')?.checked;
        const mu  = $('id_monto_unitario');
        if (mu) { mu.value = esM ? c.monto_matricula : c.monto_mensualidad; calcImporte(); }
        if (!esM && !$('id_concepto').value) {
            const opt = $('id_carrera')?.options[$('id_carrera').selectedIndex];
            if (opt) $('id_concepto').value = `Pago de cuota - ${opt.text}`;
        }
    }

    function syncMatricula() {
        const esM = $('id_es_matricula')?.checked;
        $('pfCuotas').classList.toggle('hidden', esM);
        if (esM) {
            [$('id_numero_cuota'), $('id_fecha_vencimiento')].forEach(el => { if (el) el.value = ''; });
            if ($('id_puntos'))          $('id_puntos').value = '0';
            if ($('id_cantidad_cuotas')) $('id_cantidad_cuotas').value = '1';
            const cid = $('id_carrera')?.value;
            if (cid && CM.has(cid)) {
                const c = CM.get(cid);
                if ($('id_monto_unitario')) $('id_monto_unitario').value = c.monto_matricula;
                if ($('id_importe_total'))  $('id_importe_total').value  = c.monto_matricula;
                if (!$('id_concepto').value) $('id_concepto').value = 'Pago de matrícula';
            }
        } else {
            const cid = $('id_carrera')?.value;
            if (cid && CM.has(cid)) applyCarrera(cid);
        }
    }

    function syncCliente() {
        const on = $('id_es_cliente_diferenciado')?.checked;
        $('camposAlumno').style.display    = on ? 'none'  : 'block';
        $('camposClienteDif').style.display = on ? 'block' : 'none';
        if (on) setAlumno(null, null);
    }

    function syncCarrera() {
        const sel  = $('id_carrera'); const wrap = $('pfCarreraOtroWrap'); if (!sel || !wrap) return;
        const txt  = sel.selectedIndex >= 0 ? sel.options[sel.selectedIndex].text.trim().toUpperCase() : '';
        const esOtros = sel.value === 'OTROS' || txt === 'OTROS';
        wrap.classList.toggle('open', esOtros);
        if (!esOtros && $('id_carrera_otro')) $('id_carrera_otro').value = '';
    }

    /* ── Método de pago ──────────────────────────────────── */
    function getMetodo() {
        let m = '';
        document.querySelectorAll('input[name="metodo_pago"]').forEach(r => { if (r.checked) m = r.value; });
        return m;
    }

    function syncMetodoPago(resetBanco = false) {
        const m     = getMetodo();
        const banco = $('pfBancoPanel');
        const split = $('pfSplitPanel');

        banco.classList.toggle('open', m === 'DEPOSITO');
        split.classList.toggle('open', m === 'MIXTO');

        /* Solo resetear cuando el usuario cambia manualmente el método */
        if (resetBanco) {
            cerrarOtro();
            if ($('cuentaBancariaId')) $('cuentaBancariaId').value = '';
            document.querySelectorAll('input[name="banco_seleccion"]').forEach(r => r.checked = false);
        }

        if (m !== 'DEPOSITO' && m !== 'MIXTO') {
            if ($('cuentaBancariaId')) $('cuentaBancariaId').value = '';
        }
        if (m !== 'MIXTO') {
            if ($('pfMontoEfectivo')) $('pfMontoEfectivo').value = '';
            if ($('pfMontoDeposito')) $('pfMontoDeposito').value = '';
        }
        updateSplitCheck();
    }

    function updateSplitCheck() {
        const total = parseFloat($('id_importe_total')?.value) || 0;
        const ef    = parseFloat($('pfMontoEfectivo')?.value)  || 0;
        const dep   = parseFloat($('pfMontoDeposito')?.value)  || 0;
        const chk   = $('pfSplitCheck'); if (!chk) return;
        const txt   = $('pfSplitCheckText'), amt = $('pfSplitCheckAmt');
        if (total <= 0) {
            chk.className = 'pf-split-check warn';
            txt.innerHTML = '<i class="bi bi-info-circle"></i> Ingresá el total primero';
            amt.textContent = '';
            return;
        }
        const suma = ef + dep, diff = total - suma;
        if (Math.abs(diff) < 1) {
            chk.className = 'pf-split-check ok';
            txt.innerHTML = '<i class="bi bi-check-circle-fill"></i> Cobro coincide con el total';
            amt.textContent = 'Gs. ' + total.toLocaleString('es-PY');
        } else if (suma === 0) {
            chk.className = 'pf-split-check warn';
            txt.innerHTML = '<i class="bi bi-exclamation-circle"></i> Completá el desglose';
            amt.textContent = '';
        } else if (diff > 0) {
            chk.className = 'pf-split-check warn';
            txt.innerHTML = '<i class="bi bi-exclamation-circle"></i> Faltan:';
            amt.textContent = 'Gs. ' + diff.toLocaleString('es-PY');
        } else {
            chk.className = 'pf-split-check err';
            txt.innerHTML = '<i class="bi bi-x-circle-fill"></i> Supera el total por:';
            amt.textContent = 'Gs. ' + Math.abs(diff).toLocaleString('es-PY');
        }
    }

    /* ── Banco ───────────────────────────────────────────── */
    const ICONOS = {
        continental: 'bi-bank', itau: 'bi-building-fill', vision: 'bi-eye-fill',
        familiar: 'bi-house-heart-fill', bnf: 'bi-flag-fill', interfisa: 'bi-diagram-3-fill',
        rio: 'bi-water', basa: 'bi-bar-chart-fill', atlas: 'bi-globe2'
    };

    function buildBancoCards(cuentas, gridId, cardOtroId, radioOtroId) {
        const grid = $(gridId), cardOtro = $(cardOtroId); if (!grid) return;
        grid.querySelectorAll('.pf-banco-card:not(.otro)').forEach(el => el.remove());
        const actualId = $('cuentaBancariaId')?.value;
        cuentas.forEach(c => {
            const card = document.createElement('div'); card.className = 'pf-banco-card';
            const iid  = `${gridId}_${c.id}`;
            const key  = Object.keys(ICONOS).find(k => c.entidad.toLowerCase().includes(k));
            const icon = ICONOS[key] || 'bi-bank';
            card.innerHTML = `
                <input type="radio" name="banco_seleccion" value="${c.id}" id="${iid}" ${actualId == c.id ? 'checked' : ''}>
                <label for="${iid}">
                    <span class="pf-banco-card-icon"><i class="bi ${icon}"></i></span>
                    <span class="pf-banco-card-entidad">${c.entidad}</span>
                    <span class="pf-banco-card-titular">${c.titular}</span>
                </label>`;
            card.querySelector('input').addEventListener('change', () => {
                if ($('cuentaBancariaId')) $('cuentaBancariaId').value = c.id; 
                cerrarOtro();
            });
            grid.insertBefore(card, cardOtro);
            if (actualId == c.id) { if ($('cuentaBancariaId')) $('cuentaBancariaId').value = c.id; }
        });
        $(radioOtroId)?.addEventListener('change', () => {
            if ($('cuentaBancariaId')) $('cuentaBancariaId').value = '';
            $('pfOtroBancoInputs')?.classList.add('open');
        });
    }

    function renderBancos(cuentas) {
        buildBancoCards(cuentas, 'pfBancoGrid',      'pfCardOtro',      'pfRadioOtro');
        buildBancoCards(cuentas, 'pfBancoGridMixto', 'pfCardOtroMixto', 'pfRadioOtroMixto');
    }

    function cerrarOtro() { $('pfOtroBancoInputs')?.classList.remove('open'); }

    async function guardarBanco() {
        const ent = $('pfEntidad')?.value.trim(), tit = $('pfTitular')?.value.trim();
        if (!ent || !tit) { alert('Ingresá entidad y titular.'); return; }
        const btn = $('pfBtnSave'); btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Guardando…';
        try {
            const res = await fetch('/cuentas-bancarias/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
                body: JSON.stringify({ entidad: ent, titular: tit })
            });
            const d = await res.json(); if (!d.id) throw new Error(d.error || 'Error');
            if ($('cuentaBancariaId')) $('cuentaBancariaId').value = d.id;
            if (!cuentasBancarias.find(c => c.id === d.id)) cuentasBancarias.push(d);
            renderBancos(cuentasBancarias);
            const r = document.querySelector(`input[name="banco_seleccion"][value="${d.id}"]`);
            if (r) { r.checked = true; if ($('cuentaBancariaId')) $('cuentaBancariaId').value = d.id; }
            cerrarOtro();
            btn.className = 'pf-btn-save-banco ok';
            btn.innerHTML = '<i class="bi bi-check-circle-fill"></i> Guardado';
        } catch (err) {
            alert('No se pudo guardar: ' + err.message);
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-floppy"></i> Guardar para futuros pagos';
        }
    }

    /* ── Alumno dropdown ─────────────────────────────────── */
    let alumnoDropdownOpen = false;
    let alumnoFocusedIdx   = -1;
    let alumnoResults      = [];
    let alumnoRecents      = [];

    function positionAlumnoDropdown() {
        const trigger  = $('alumnoTrigger');
        const dropdown = $('alumnoDropdown');
        if (!trigger || !dropdown) return;
        const rect = trigger.getBoundingClientRect();
        dropdown.style.top   = (rect.bottom + 5) + 'px';
        dropdown.style.left  = rect.left + 'px';
        dropdown.style.width = rect.width + 'px';
        const maxH = Math.max(180, Math.min(320, window.innerHeight - rect.bottom - 16));
        dropdown.style.maxHeight = maxH + 'px';
        const list = dropdown.querySelector('.pf-alumno-list');
        if (list) list.style.maxHeight = (maxH - 62) + 'px';
    }

    function initAlumnoDropdownPortal() {
        const dd = $('alumnoDropdown');
        if (dd && dd.parentElement !== document.body) document.body.appendChild(dd);
    }

    function setAlumno(id, label, data) {
        const inp = $('id_alumno'), trig = $('alumnoTrigger'), txt = $('alumnoTriggerText');
        if (id) {
            inp.value = id;
            txt.textContent = label;
            trig.classList.add('has-value');
            if (data) {
                if (data.sede_id)    $('id_sede').value = data.sede_id;
                if (data.carrera_id) { $('id_carrera').value = data.carrera_id; applyCarrera(data.carrera_id); syncCarrera(); }
            }
            setTimeout(() => advanceTo($('id_sede')), 100);
        } else {
            inp.value = '';
            txt.textContent = 'Seleccioná un alumno…';
            trig.classList.remove('has-value');
        }
        closeAlumnoDropdown();
    }

    function openAlumnoDropdown() {
        alumnoDropdownOpen = true;
        positionAlumnoDropdown();
        $('alumnoDropdown').classList.add('open');
        $('alumnoTrigger').classList.add('open');
        $('alumnoTrigger').setAttribute('aria-expanded', 'true');
        setTimeout(() => { $('alumnoSearch').focus(); }, 60);
        if (alumnoRecents.length === 0 && !$('alumnoSearch').value) loadRecientes();
        else if (!$('alumnoSearch').value) renderAlumnoOptions(alumnoRecents, true);
    }

    function closeAlumnoDropdown() {
        alumnoDropdownOpen = false;
        $('alumnoDropdown').classList.remove('open');
        $('alumnoTrigger').classList.remove('open');
        $('alumnoTrigger').setAttribute('aria-expanded', 'false');
        alumnoFocusedIdx = -1;
    }

    async function loadRecientes() {
        const list = $('alumnoList');
        list.innerHTML = '<div class="pf-alumno-loading"><i class="bi bi-hourglass-split"></i> Cargando…</div>';
        try {
            const res  = await fetch('/buscar-alumno/?q=&recientes=1');
            const data = (await res.json()).resultados || [];
            alumnoRecents = data;
            renderAlumnoOptions(data, true);
        } catch {
            list.innerHTML = '<div class="pf-alumno-empty"><i class="bi bi-exclamation-circle"></i> Error al cargar</div>';
        }
    }

    function renderAlumnoOptions(data, isRecent = false) {
        alumnoResults = data;
        const list = $('alumnoList');
        if (!data.length) {
            list.innerHTML = '<div class="pf-alumno-empty">Sin resultados — probá con otro término</div>';
            return;
        }
        const header = isRecent
            ? '<div style="padding:.4rem 1rem .2rem;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--gray-400);"><i class="bi bi-clock-history"></i> Recientes</div>'
            : '';
        list.innerHTML = header + data.map((a, i) => `
            <div class="pf-alumno-option" data-idx="${i}" role="option">
                <div class="pf-alumno-option-name">${a.nombre_completo}</div>
                <div class="pf-alumno-option-detail">
                    <span><i class="bi bi-person-badge"></i> ${a.cedula || 'Sin cédula'}</span>
                    ${a.sede   ? `<span><i class="bi bi-building"></i> ${a.sede}</span>`   : ''}
                    ${a.carrera ? `<span><i class="bi bi-book"></i> ${a.carrera}</span>` : ''}
                </div>
            </div>`).join('');
        list.querySelectorAll('.pf-alumno-option').forEach((el, i) => {
            el.addEventListener('mousedown', e => { e.preventDefault(); selectAlumnoByIdx(i); });
        });
    }

    function selectAlumnoByIdx(i) {
        const a = alumnoResults[i]; if (!a) return;
        setAlumno(a.id, `${a.nombre_completo}${a.cedula ? ' (' + a.cedula + ')' : ''}`, a);
    }

    function highlightOption(idx) {
        const opts = $('alumnoList').querySelectorAll('.pf-alumno-option');
        opts.forEach(o => o.classList.remove('focused'));
        if (idx >= 0 && idx < opts.length) { opts[idx].classList.add('focused'); opts[idx].scrollIntoView({ block: 'nearest' }); }
        alumnoFocusedIdx = idx;
    }

    async function searchAlumnos(q) {
        const list = $('alumnoList');
        if (!q || q.length < 1) { renderAlumnoOptions(alumnoRecents, true); return; }
        list.innerHTML = '<div class="pf-alumno-loading"><i class="bi bi-hourglass-split"></i> Buscando…</div>';
        try {
            const res  = await fetch(`/buscar-alumno/?q=${encodeURIComponent(q)}`);
            const data = (await res.json()).resultados || [];
            renderAlumnoOptions(data, false);
        } catch {
            list.innerHTML = '<div class="pf-alumno-empty">Error al buscar</div>';
        }
    }

    /* ── Modal imagen ────────────────────────────────────── */
    window.abrirModalImg = function (url) {
        $('imgModalGrande').src = url;
        new bootstrap.Modal($('modalImg')).show();
    };

    /* ── Validación submit ───────────────────────────────── */
    function validarYEnviar(e) {
        const v = parseFloat($('id_importe_total')?.value);
        if (!v || v <= 0) {
            e.preventDefault(); $('id_importe_total')?.focus();
            alert('El importe debe ser mayor a 0.'); return;
        }
        const m = getMetodo();
        if (m === 'DEPOSITO' || m === 'MIXTO') {
            const br = document.querySelector('input[name="banco_seleccion"]:checked');
            if (!br) { e.preventDefault(); alert('Seleccioná la cuenta bancaria destino.'); return; }
            if (br.value === 'OTRO') {
                const ent = $('pfEntidad')?.value.trim(), tit = $('pfTitular')?.value.trim();
                if (!ent || !tit) { e.preventDefault(); alert('Completá entidad y titular del banco.'); return; }
                const f = $('pagoForm');
                ['otro_banco_entidad', 'otro_banco_titular'].forEach((n, i) => {
                    let h = document.createElement('input');
                    h.type = 'hidden'; h.name = n; h.value = [ent, tit][i]; f.appendChild(h);
                });
            }
        }
    }

    /* ── Init ────────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', () => {
        /* Fecha por defecto hoy */
        $('btnHoy')?.addEventListener('click', () => {
            $('id_fecha').value = new Date().toISOString().split('T')[0];
        });
        if (!$('id_fecha')?.value) $('id_fecha').value = new Date().toISOString().split('T')[0];

        /* Portal dropdown alumno */
        initAlumnoDropdownPortal();

        /* Sync inicial */
        syncCliente(); syncMatricula(); syncMetodoPago(); syncCarrera();
        renderBancos(cuentasBancarias);
        setupEnterAdvance();

        /* Repositionar dropdown en scroll/resize */
        window.addEventListener('scroll', () => { if (alumnoDropdownOpen) positionAlumnoDropdown(); }, { passive: true });
        window.addEventListener('resize', () => { if (alumnoDropdownOpen) positionAlumnoDropdown(); }, { passive: true });

        /* Alumno dropdown */
        $('alumnoTrigger')?.addEventListener('click', e => {
            if (e.target.closest('#alumnoClear')) return;
            alumnoDropdownOpen ? closeAlumnoDropdown() : openAlumnoDropdown();
        });
        $('alumnoTrigger')?.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); alumnoDropdownOpen ? closeAlumnoDropdown() : openAlumnoDropdown(); }
            if (e.key === 'Escape')    closeAlumnoDropdown();
            if (e.key === 'ArrowDown') { e.preventDefault(); if (!alumnoDropdownOpen) openAlumnoDropdown(); }
        });
        $('alumnoClear')?.addEventListener('click', e => { e.stopPropagation(); setAlumno(null, null); });
        $('alumnoSearch')?.addEventListener('input', deb(e => searchAlumnos(e.target.value.trim()), 250));
        $('alumnoSearch')?.addEventListener('keydown', e => {
            const opts = alumnoResults;
            if (e.key === 'ArrowDown') { e.preventDefault(); highlightOption(Math.min(alumnoFocusedIdx + 1, opts.length - 1)); }
            if (e.key === 'ArrowUp')   { e.preventDefault(); highlightOption(Math.max(alumnoFocusedIdx - 1, 0)); }
            if (e.key === 'Enter')     { e.preventDefault(); if (alumnoFocusedIdx >= 0) selectAlumnoByIdx(alumnoFocusedIdx); }
            if (e.key === 'Escape')    { closeAlumnoDropdown(); $('alumnoTrigger').focus(); }
            if (e.key === 'Tab')       closeAlumnoDropdown();
        });
        document.addEventListener('mousedown', e => {
            if (!e.target.closest('.pf-alumno-select') && !e.target.closest('#alumnoDropdown'))
                closeAlumnoDropdown();
        });

        /* Eventos del form */
        $('id_es_matricula')?.addEventListener('change', syncMatricula);
        $('id_es_cliente_diferenciado')?.addEventListener('change', syncCliente);
        $('id_carrera')?.addEventListener('change', () => { applyCarrera($('id_carrera').value); syncCarrera(); });
        document.querySelectorAll('input[name="metodo_pago"]').forEach(r => r.addEventListener('change', () => syncMetodoPago(true)));
        $('pfBtnSave')?.addEventListener('click', guardarBanco);
        $('id_monto_unitario')?.addEventListener('input', calcImporte);
        $('id_cantidad_cuotas')?.addEventListener('input', calcImporte);
        $('id_importe_total')?.addEventListener('input', updateSplitCheck);
        $('pfMontoEfectivo')?.addEventListener('input', updateSplitCheck);
        $('pfMontoDeposito')?.addEventListener('input', updateSplitCheck);

        /* URL params */
        const p = new URLSearchParams(location.search);
        if (p.get('alumno') && $('id_alumno')) $('id_alumno').value = p.get('alumno');
        if (p.get('nombre')) {
            const trig = $('alumnoTrigger'), txt = $('alumnoTriggerText');
            if (trig && txt) { txt.textContent = decodeURIComponent(p.get('nombre')); trig.classList.add('has-value'); }
        }
        if (p.get('sede')    && $('id_sede'))    $('id_sede').value = p.get('sede');
        if (p.get('carrera') && $('id_carrera')) { $('id_carrera').value = p.get('carrera'); applyCarrera(p.get('carrera')); syncCarrera(); }

        /* Preview imagen */
        $('id_foto_comprobante')?.addEventListener('change', e => {
            const f = e.target.files[0]; if (!f) return;
            const r = new FileReader();
            r.onload = ev => {
                const img = $('imagenPreview'), cont = $('previewContainer');
                if (img) img.src = ev.target.result;
                if (cont) cont.style.display = 'block';
            };
            r.readAsDataURL(f);
        });

        /* Submit */
        $('pagoForm')?.addEventListener('submit', validarYEnviar);
    });

})();