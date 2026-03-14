/* formEgresos.js — ITS CEP */
(function () {
    'use strict';

    /* ── Guard ──────────────────────────────────────────── */
    if (document.body.dataset.efInit) return;
    document.body.dataset.efInit = '1';

    /* ── Helpers ────────────────────────────────────────── */
    const $ = id => document.getElementById(id);

    /* ── Auto-advance con Enter ──────────────────────────── */
    function isVisible(el) {
        if (!el) return false;
        const s = window.getComputedStyle(el);
        return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetParent !== null && !el.disabled;
    }

    function getAllFocusable() {
        return Array.from(document.querySelectorAll(
            '#formEgreso input:not([type=hidden]):not([type=radio]):not([type=checkbox]),' +
            '#formEgreso select,' +
            '#formEgreso textarea'
        )).filter(isVisible);
    }

    function getNextFocusable(currentEl) {
        const all = getAllFocusable();
        const idx = all.indexOf(currentEl);
        return idx < 0 ? null : (all[idx + 1] || null);
    }

    function advanceTo(el) {
        if (!el) return;
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => el.focus(), 120);
    }

    function setupEnterAdvance() {
        $('formEgreso')?.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter') return;
            if (e.target.tagName === 'TEXTAREA') return;
            if (e.target.type === 'submit') return;
            e.preventDefault();
            const next = getNextFocusable(e.target);
            if (next) advanceTo(next);
        });

        /* Fecha → siguiente campo al elegir con el date picker */
        $('id_fecha')?.addEventListener('change', () => {
            const next = getNextFocusable($('id_fecha'));
            if (next) setTimeout(() => advanceTo(next), 80);
        });

        /* Sede → Categoría */
        $('id_sede')?.addEventListener('change', () => {
            setTimeout(() => advanceTo($('id_categoria_egreso')), 60);
        });

        /* Categoría → Concepto (o funcionario si es SUELDOS) */
        $('id_categoria_egreso')?.addEventListener('change', () => {
            setTimeout(() => {
                const esSueldo = $('id_categoria_egreso')?.value === 'SUELDOS';
                const next = esSueldo ? $('id_funcionario') : $('id_concepto');
                if (isVisible(next)) advanceTo(next);
            }, 120);
        });
    }

    /* ── Monto en tiempo real ────────────────────────────── */
    function actualizarMonto() {
        const valor       = parseFloat($('id_monto')?.value) || 0;
        const montoDisplay = $('montoDisplay');
        if (montoDisplay) {
            montoDisplay.textContent = valor > 0 ? valor.toLocaleString('es-PY') : '0';
        }
    }

    /* ── Funcionario: mostrar/ocultar según categoría ────── */
    function toggleFuncionario() {
        const cat      = $('id_categoria_egreso');
        const bloque   = $('bloqueFunc');
        const selectF  = $('id_funcionario');
        if (!cat || !bloque) return;

        const esSueldo = cat.value === 'SUELDOS';
        bloque.classList.toggle('visible', esSueldo);

        /* Limpiar la selección cuando no aplica */
        if (!esSueldo && selectF) selectF.value = '';
    }

    /* ── Preview de comprobante ──────────────────────────── */
    function setupPreview() {
        $('id_comprobante')?.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function (ev) {
                const img  = $('imagenPreview');
                const cont = $('previewContainer');
                if (img)  img.src = ev.target.result;
                if (cont) cont.style.display = 'block';
            };
            reader.readAsDataURL(file);
        });
    }

    /* ── Funcionario dropdown ────────────────────────────── */
    const deb = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

    let funcDropdownOpen = false;
    let funcFocusedIdx   = -1;
    let funcResults      = [];
    let funcRecents      = [];

    function positionFuncDropdown() {
        const trigger  = $('funcTrigger');
        const dropdown = $('funcDropdown');
        if (!trigger || !dropdown) return;
        const rect = trigger.getBoundingClientRect();
        dropdown.style.top   = (rect.bottom + 5) + 'px';
        dropdown.style.left  = rect.left + 'px';
        dropdown.style.width = rect.width + 'px';
        const maxH = Math.max(180, Math.min(320, window.innerHeight - rect.bottom - 16));
        dropdown.style.maxHeight = maxH + 'px';
        const list = dropdown.querySelector('.ef-func-list');
        if (list) list.style.maxHeight = (maxH - 62) + 'px';
    }

    function initFuncDropdownPortal() {
        const dd = $('funcDropdown');
        if (dd && dd.parentElement !== document.body) document.body.appendChild(dd);
    }

    function setFuncionario(id, label) {
        const inp  = $('id_funcionario');
        const trig = $('funcTrigger');
        const txt  = $('funcTriggerText');
        if (id) {
            if (inp)  inp.value = id;
            if (txt)  txt.textContent = label;
            if (trig) trig.classList.add('has-value');
            setTimeout(() => advanceTo($('id_concepto')), 100);
        } else {
            if (inp)  inp.value = '';
            if (txt)  txt.textContent = 'Seleccioná un funcionario…';
            if (trig) trig.classList.remove('has-value');
        }
        closeFuncDropdown();
    }

    function openFuncDropdown() {
        funcDropdownOpen = true;
        positionFuncDropdown();
        $('funcDropdown')?.classList.add('open');
        $('funcTrigger')?.classList.add('open');
        $('funcTrigger')?.setAttribute('aria-expanded', 'true');
        setTimeout(() => $('funcSearch')?.focus(), 60);
        if (funcRecents.length === 0 && !$('funcSearch')?.value) loadFuncRecientes();
        else if (!$('funcSearch')?.value) renderFuncOptions(funcRecents, true);
    }

    function closeFuncDropdown() {
        funcDropdownOpen = false;
        $('funcDropdown')?.classList.remove('open');
        $('funcTrigger')?.classList.remove('open');
        $('funcTrigger')?.setAttribute('aria-expanded', 'false');
        funcFocusedIdx = -1;
    }

    async function loadFuncRecientes() {
        const list = $('funcList');
        if (!list) return;
        list.innerHTML = '<div class="ef-func-loading"><i class="bi bi-hourglass-split"></i> Cargando…</div>';
        try {
            const res  = await fetch('/buscar-funcionario/?q=&recientes=1');
            const data = (await res.json()).resultados || [];
            funcRecents = data;
            renderFuncOptions(data, true);
        } catch {
            list.innerHTML = '<div class="ef-func-empty"><i class="bi bi-exclamation-circle"></i> Error al cargar</div>';
        }
    }

    function renderFuncOptions(data, isRecent = false) {
        funcResults = data;
        const list  = $('funcList');
        if (!list) return;
        if (!data.length) {
            list.innerHTML = '<div class="ef-func-empty">Sin resultados — probá con otro nombre</div>';
            return;
        }
        const header = isRecent
            ? '<div style="padding:.4rem 1rem .2rem;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--gray-400);"><i class="bi bi-clock-history"></i> Recientes</div>'
            : '';
        list.innerHTML = header + data.map((f, i) => `
            <div class="ef-func-option" data-idx="${i}" role="option">
                <div class="ef-func-option-name">${f.nombre_completo}</div>
                <div class="ef-func-option-detail">
                    ${f.cargo  ? `<span><i class="bi bi-briefcase"></i> ${f.cargo}</span>`    : ''}
                    ${f.sede   ? `<span><i class="bi bi-building"></i> ${f.sede}</span>`      : ''}
                    ${f.cedula ? `<span><i class="bi bi-person-badge"></i> ${f.cedula}</span>` : ''}
                </div>
            </div>`).join('');
        list.querySelectorAll('.ef-func-option').forEach((el, i) => {
            el.addEventListener('mousedown', e => { e.preventDefault(); selectFuncByIdx(i); });
        });
    }

    function selectFuncByIdx(i) {
        const f = funcResults[i]; if (!f) return;
        setFuncionario(f.id, f.nombre_completo + (f.cargo ? ` — ${f.cargo}` : ''));
    }

    function highlightFuncOption(idx) {
        const opts = $('funcList')?.querySelectorAll('.ef-func-option');
        if (!opts) return;
        opts.forEach(o => o.classList.remove('focused'));
        if (idx >= 0 && idx < opts.length) {
            opts[idx].classList.add('focused');
            opts[idx].scrollIntoView({ block: 'nearest' });
        }
        funcFocusedIdx = idx;
    }

    async function searchFuncionarios(q) {
        const list = $('funcList');
        if (!list) return;
        if (!q || q.length < 1) { renderFuncOptions(funcRecents, true); return; }
        list.innerHTML = '<div class="ef-func-loading"><i class="bi bi-hourglass-split"></i> Buscando…</div>';
        try {
            const res  = await fetch(`/buscar-funcionario/?q=${encodeURIComponent(q)}`);
            const data = (await res.json()).resultados || [];
            renderFuncOptions(data, false);
        } catch {
            list.innerHTML = '<div class="ef-func-empty">Error al buscar</div>';
        }
    }

    function setupFuncDropdown() {
        initFuncDropdownPortal();

        window.addEventListener('scroll', () => { if (funcDropdownOpen) positionFuncDropdown(); }, { passive: true });
        window.addEventListener('resize', () => { if (funcDropdownOpen) positionFuncDropdown(); }, { passive: true });

        $('funcTrigger')?.addEventListener('click', e => {
            if (e.target.closest('#funcClear')) return;
            funcDropdownOpen ? closeFuncDropdown() : openFuncDropdown();
        });

        $('funcTrigger')?.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); funcDropdownOpen ? closeFuncDropdown() : openFuncDropdown(); }
            if (e.key === 'Escape')    closeFuncDropdown();
            if (e.key === 'ArrowDown') { e.preventDefault(); if (!funcDropdownOpen) openFuncDropdown(); }
        });

        $('funcClear')?.addEventListener('click', e => { e.stopPropagation(); setFuncionario(null, null); });

        $('funcSearch')?.addEventListener('input', deb(e => searchFuncionarios(e.target.value.trim()), 250));

        $('funcSearch')?.addEventListener('keydown', e => {
            if (e.key === 'ArrowDown') { e.preventDefault(); highlightFuncOption(Math.min(funcFocusedIdx + 1, funcResults.length - 1)); }
            if (e.key === 'ArrowUp')   { e.preventDefault(); highlightFuncOption(Math.max(funcFocusedIdx - 1, 0)); }
            if (e.key === 'Enter')     { e.preventDefault(); if (funcFocusedIdx >= 0) selectFuncByIdx(funcFocusedIdx); }
            if (e.key === 'Escape')    { closeFuncDropdown(); $('funcTrigger')?.focus(); }
            if (e.key === 'Tab')       closeFuncDropdown();
        });

        document.addEventListener('mousedown', e => {
            if (!e.target.closest('.ef-func-select') && !e.target.closest('#funcDropdown'))
                closeFuncDropdown();
        });

        /* Prellenar trigger si hay funcionario en edición */
        const inp = $('id_funcionario');
        if (inp?.value) {
            const optEl = document.querySelector(`#id_funcionario_hidden option[value="${inp.value}"]`);
            if (optEl) {
                $('funcTriggerText').textContent = optEl.textContent.trim();
                $('funcTrigger')?.classList.add('has-value');
            }
        }
    }

    /* ── Modal imagen ────────────────────────────────────── */
    window.abrirModalImg = function (url) {
        $('imgModalGrande').src = url;
        new bootstrap.Modal($('modalImg')).show();
    };

    /* ── Validación submit ───────────────────────────────── */
    function validarYEnviar(e) {
        const monto = parseFloat($('id_monto')?.value) || 0;
        if (monto <= 0) {
            e.preventDefault();
            $('id_monto')?.focus();

            /* Mostrar mensaje solo una vez */
            if (!document.querySelector('.ef-error-monto')) {
                const err = document.createElement('div');
                err.className = 'ef-error-message ef-error-monto';
                err.innerHTML = '<i class="bi bi-exclamation-circle"></i> El monto debe ser mayor a 0';
                $('id_monto')?.closest('.ef-field')?.appendChild(err);
            }
        }
    }

    /* ── Init ────────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', () => {
        /* Fecha por defecto hoy */
        $('btnHoy')?.addEventListener('click', () => {
            $('id_fecha').value = new Date().toISOString().split('T')[0];
        });
        if (!$('id_fecha')?.value) {
            $('id_fecha').value = new Date().toISOString().split('T')[0];
        }

        /* Monto en tiempo real */
        $('id_monto')?.addEventListener('input', actualizarMonto);
        actualizarMonto();

        /* Funcionario */
        $('id_categoria_egreso')?.addEventListener('change', toggleFuncionario);
        toggleFuncionario(); /* ejecutar al cargar para edición */

        /* Resto */
        setupEnterAdvance();
        setupPreview();
        setupFuncDropdown();

        $('formEgreso')?.addEventListener('submit', validarYEnviar);
    });

})();