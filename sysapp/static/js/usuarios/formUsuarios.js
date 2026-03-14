(function () {
    const $  = id => document.getElementById(id);
    const $$ = sel => [...document.querySelectorAll(sel)];

    /* ─── Refs ──────────────────────────────────────────── */
    const modal       = $('modal-roles');
    const btnAbrir    = $('btn-abrir-modal');
    const btnCerrar   = $('btn-cerrar');
    const btnCancelar = $('btn-cancelar');
    const btnAplicar  = $('btn-aplicar');
    const mSearch     = $('m-search');
    const mEmpty      = $('m-empty');
    const mCount      = $('m-count');
    const chipsArea   = $('chips-area');
    const chipsEmpty  = $('chips-empty');
    const rolesInputs = $('roles-inputs');

    /* ─── Estado ────────────────────────────────────────── */
    let confirmed = new Set();
    let tempSel   = new Set();
    let allItems  = $$('.m-item[data-id]');

    /* Inicializar desde Django (ítems pre-seleccionados) */
    allItems.forEach(item => {
        if (item.classList.contains('sel')) confirmed.add(item.dataset.id);
    });
    renderChips(confirmed);
    syncHiddenInputs(confirmed);

    /* ─── Enrich modal items ──────────────────────────────
       Lee data-permcount del ítem (si lo pasa Django)
       y muestra el badge de cantidad de permisos.
    ─────────────────────────────────────────────────────── */
    function enrichRoleItems() {
        allItems.forEach(item => {
            const meta = item.querySelector('.m-item-meta');
            if (!meta) return;

            /* Si el template incluye data-permcount, mostrarlo */
            const count = item.dataset.permcount;
            if (count !== undefined && !meta.querySelector('.m-perm-count')) {
                const badge = document.createElement('span');
                badge.className = `m-perm-count ${count === '0' ? 'zero' : ''}`;
                badge.innerHTML = `<i class="bi bi-toggles"></i> ${count} permiso${count !== '1' ? 's' : ''}`;
                meta.appendChild(badge);
            }
        });
    }

    /* ─── Modal open / close ────────────────────────────── */
    function openModal() {
        tempSel = new Set(confirmed);
        syncItemStates();
        updateCount();
        mSearch.value = '';
        filterItems('');
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
        setTimeout(() => mSearch.focus(), 250);
    }

    function closeModal(apply) {
        if (apply) {
            confirmed = new Set(tempSel);
            renderChips(confirmed);
            syncHiddenInputs(confirmed);
        }
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }

    btnAbrir.addEventListener('click', openModal);
    btnCerrar.addEventListener('click', () => closeModal(false));
    btnCancelar.addEventListener('click', () => closeModal(false));
    btnAplicar.addEventListener('click', () => closeModal(true));
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(false); });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && modal.classList.contains('open')) closeModal(false);
    });

    /* ─── Toggle item ───────────────────────────────────── */
    function bindItem(item) {
        item.addEventListener('click', () => toggleItem(item));
        item.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleItem(item); }
        });
    }
    allItems.forEach(bindItem);

    function toggleItem(item) {
        const id = item.dataset.id;
        if (tempSel.has(id)) {
            tempSel.delete(id);
            item.classList.remove('sel');
            item.setAttribute('aria-checked', 'false');
        } else {
            tempSel.add(id);
            item.classList.add('sel');
            item.setAttribute('aria-checked', 'true');
        }
        updateCount();
    }

    function syncItemStates() {
        allItems.forEach(item => {
            const sel = tempSel.has(item.dataset.id);
            item.classList.toggle('sel', sel);
            item.setAttribute('aria-checked', String(sel));
        });
    }

    function updateCount() { mCount.textContent = tempSel.size; }

    /* ─── Search ────────────────────────────────────────── */
    mSearch.addEventListener('input', function () { filterItems(this.value.trim().toLowerCase()); });

    function filterItems(term) {
        let visible = 0;
        allItems.forEach(item => {
            const match = !term || item.dataset.name.toLowerCase().includes(term);
            item.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        mEmpty.style.display = visible === 0 ? 'block' : 'none';
    }

    /* ─── Chips ─────────────────────────────────────────── */
    function renderChips(ids) {
        chipsArea.querySelectorAll('.fu-chip').forEach(c => c.remove());
        ids.forEach(id => {
            const item = allItems.find(i => i.dataset.id === id);
            if (!item) return;

            const count = item.dataset.permcount;
            const countHtml = count !== undefined
                ? `<span class="fu-chip-pcount">(${count} perm.)</span>`
                : '';

            const chip = document.createElement('span');
            chip.className = 'fu-chip';
            chip.innerHTML = `
                <i class="bi bi-shield-check"></i>
                ${item.dataset.name}
                ${countHtml}
                <button type="button" class="fu-chip-del" data-id="${id}"
                        aria-label="Quitar ${item.dataset.name}">
                    <i class="bi bi-x"></i>
                </button>`;
            chipsArea.insertBefore(chip, chipsEmpty);
        });
        chipsEmpty.style.display = ids.size === 0 ? '' : 'none';

        chipsArea.querySelectorAll('.fu-chip-del').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                confirmed.delete(id);
                tempSel.delete(id);
                renderChips(confirmed);
                syncHiddenInputs(confirmed);
                if (modal.classList.contains('open')) { syncItemStates(); updateCount(); }
            });
        });
    }

    /* ─── Hidden inputs ─────────────────────────────────── */
    function syncHiddenInputs(ids) {
        rolesInputs.innerHTML = '';
        ids.forEach(id => {
            const inp = document.createElement('input');
            inp.type = 'hidden'; inp.name = 'roles'; inp.value = id;
            rolesInputs.appendChild(inp);
        });
    }

    /* ─── Create quick role ─────────────────────────────── */
    const btnToggle  = $('btn-toggle-crear');
    const crearForm  = $('crear-form');
    const crearInput = $('nuevo-rol-nombre');
    const btnCrear   = $('btn-crear-rol');

    btnToggle.addEventListener('click', () => {
        crearForm.classList.toggle('open');
        if (crearForm.classList.contains('open')) crearInput.focus();
    });

    btnCrear.addEventListener('click', crearRolRapido);
    crearInput.addEventListener('keydown', e => { if (e.key === 'Enter') crearRolRapido(); });

    function crearRolRapido() {
        const nombre = crearInput.value.trim();
        if (!nombre) { crearInput.focus(); return; }

        const fakeId  = 'tmp-' + Date.now();
        const list    = $('m-list');
        const newItem = document.createElement('div');
        newItem.className = 'm-item sel';
        newItem.dataset.id   = fakeId;
        newItem.dataset.name = nombre;
        newItem.dataset.permcount = '0';
        newItem.setAttribute('tabindex', '0');
        newItem.setAttribute('role', 'checkbox');
        newItem.setAttribute('aria-checked', 'true');
        newItem.innerHTML = `
            <div class="m-checkbox"><i class="bi bi-check"></i></div>
            <div class="m-item-info">
                <div class="m-item-name">${nombre}</div>
                <div class="m-item-meta">
                    <span class="m-perm-count zero"><i class="bi bi-toggles"></i> Sin permisos</span>
                    &nbsp;·&nbsp;
                    <span style="font-style:italic; font-size:.72rem;">Nuevo — guardá para persistir</span>
                </div>
            </div>`;
        list.insertBefore(newItem, mEmpty);
        bindItem(newItem);
        allItems.push(newItem);
        tempSel.add(fakeId);
        updateCount();
        crearInput.value = '';
        crearForm.classList.remove('open');
        filterItems(mSearch.value.trim().toLowerCase());
    }

    /* ─── Apply fu-input class to Django widgets ────────── */
    document.querySelectorAll(
        '.fu input:not([type=checkbox]):not([type=hidden]):not([type=radio]),.fu select,.fu textarea'
    ).forEach(el => el.classList.add('fu-input'));

    /* ─── Password strength indicator ──────────────────── */
    const pwd  = document.querySelector('input[name="password"]');
    const pwd2 = document.querySelector('input[name="password_confirm"]');

    if (pwd) {
        /* Inyectar barra de fortaleza debajo del campo */
        const pwdField = pwd.closest('.fu-field');
        if (pwdField) {
            const bar = document.createElement('div');
            bar.className = 'fu-pwd-strength';
            bar.innerHTML = `
                <div class="fu-pwd-bar"><div class="fu-pwd-fill" id="pwd-fill"></div></div>
                <div class="fu-pwd-label" id="pwd-label" style="color:var(--lc-muted);"></div>`;
            pwdField.appendChild(bar);
        }

        pwd.addEventListener('input', () => {
            const val   = pwd.value;
            const fill  = $('pwd-fill');
            const label = $('pwd-label');
            if (!fill || !val) {
                if (fill)  { fill.style.width = '0'; fill.className = 'fu-pwd-fill'; }
                if (label) label.textContent = '';
                return;
            }
            let score = 0;
            if (val.length >= 8)  score++;
            if (val.length >= 12) score++;
            if (/[A-Z]/.test(val)) score++;
            if (/[0-9]/.test(val)) score++;
            if (/[^A-Za-z0-9]/.test(val)) score++;

            const levels = [
                { min:0, cls:'weak',   pct:'20%', text:'Muy débil',  color:'var(--lc-red)' },
                { min:1, cls:'weak',   pct:'35%', text:'Débil',      color:'var(--lc-red)' },
                { min:2, cls:'medium', pct:'55%', text:'Aceptable',  color:'#d97706' },
                { min:3, cls:'medium', pct:'70%', text:'Buena',      color:'#d97706' },
                { min:4, cls:'strong', pct:'85%', text:'Fuerte',     color:'var(--lc-green)' },
                { min:5, cls:'strong', pct:'100%',text:'Muy fuerte', color:'var(--lc-green)' },
            ];
            const lvl = levels[Math.min(score, levels.length - 1)];
            fill.style.width = lvl.pct;
            fill.className   = `fu-pwd-fill ${lvl.cls}`;
            label.textContent = lvl.text;
            label.style.color = lvl.color;
        });
    }

    /* ─── Password match validation ─────────────────────── */
    if (pwd && pwd2) {
        function validarPwd() {
            const parent = pwd2.closest('.fu-field');
            let msg = parent.querySelector('.pw-error');
            if (pwd.value && pwd2.value && pwd.value !== pwd2.value) {
                if (!msg) {
                    msg = document.createElement('div');
                    msg.className = 'fu-error pw-error';
                    msg.innerHTML = '<i class="bi bi-exclamation-circle"></i> Las contraseñas no coinciden';
                    parent.appendChild(msg);
                }
            } else if (msg) {
                msg.remove();
            }
        }
        [pwd, pwd2].forEach(el => el.addEventListener('input', validarPwd));
    }

    /* ─── Init ──────────────────────────────────────────── */
    enrichRoleItems();
})();