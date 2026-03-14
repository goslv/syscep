(function () {
    if (document.body.dataset.frRolesInit) return;
    document.body.dataset.frRolesInit = '1';
    const $  = id  => document.getElementById(id);
    const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

    const MODULE_META = [
        {
            keys: ['user', 'usuario'],
            icon: 'bi-person-fill', color: '#0756a3',
            desc: 'Cuentas de acceso al sistema. Controla quién puede iniciar sesión, con qué contraseña y qué permisos directos tiene cada persona.',
            ops: [
                { cls: 'add',    text: 'Crear nuevos usuarios (nombre, email, contraseña)' },
                { cls: 'change', text: 'Cambiar datos, contraseña o estado activo/inactivo' },
                { cls: 'delete', text: 'Eliminar una cuenta permanentemente' },
                { cls: 'view',   text: 'Ver el listado y los datos de todos los usuarios' },
            ],
            warn: 'Acceso sensible — permite crear o modificar cuentas con privilegios elevados.'
        },
        {
            keys: ['alumno', 'student', 'estudiante'],
            icon: 'bi-mortarboard-fill', color: '#059669',
            desc: 'Fichas y legajos de los alumnos de la institución. Contiene datos personales, de contacto y estado académico.',
            ops: [
                { cls: 'add',    text: 'Registrar un alumno nuevo en el sistema' },
                { cls: 'change', text: 'Editar datos personales, dirección o documentos' },
                { cls: 'delete', text: 'Eliminar la ficha de un alumno' },
                { cls: 'view',   text: 'Consultar el listado y los datos de cada alumno' },
            ]
        },
        {
            keys: ['pago', 'payment', 'cobro'],
            icon: 'bi-cash-stack', color: '#d97706',
            desc: 'Registro de cobros realizados a los alumnos. Cada pago se refleja directamente en el libro de caja del día.',
            ops: [
                { cls: 'add',    text: 'Registrar un nuevo cobro a un alumno' },
                { cls: 'change', text: 'Corregir el importe, método o fecha de un pago' },
                { cls: 'delete', text: 'Anular o eliminar un pago registrado' },
                { cls: 'view',   text: 'Ver el historial de cobros y los comprobantes' },
            ]
        },
        {
            keys: ['caja'],
            icon: 'bi-safe-fill', color: '#d97706',
            desc: 'Libro de caja diaria por sede. Registra la apertura, el cierre y el balance de ingresos y egresos de cada jornada.',
            ops: [
                { cls: 'add',    text: 'Abrir una nueva caja para el día' },
                { cls: 'change', text: 'Modificar datos de apertura o cierre' },
                { cls: 'delete', text: 'Eliminar el registro de caja de un día' },
                { cls: 'view',   text: 'Consultar el balance e historial de cajas' },
            ]
        },
        {
            keys: ['egreso', 'gasto', 'expense'],
            icon: 'bi-arrow-down-circle-fill', color: '#dc2626',
            desc: 'Salidas de dinero de caja: compras de materiales, servicios contratados y gastos operativos de la sede.',
            ops: [
                { cls: 'add',    text: 'Registrar un nuevo gasto o egreso' },
                { cls: 'change', text: 'Modificar el concepto, monto o fecha de un egreso' },
                { cls: 'delete', text: 'Eliminar un egreso registrado' },
                { cls: 'view',   text: 'Ver el historial de gastos por fecha y sede' },
            ]
        },
        {
            keys: ['sede', 'sucursal', 'branch'],
            icon: 'bi-building-fill', color: '#0891b2',
            desc: 'Sedes o sucursales físicas de la institución. Cada caja, alumno e inscripción pertenece a una sede.',
            ops: [
                { cls: 'add',    text: 'Crear una nueva sede con su nombre y dirección' },
                { cls: 'change', text: 'Editar datos de contacto o nombre de la sede' },
                { cls: 'delete', text: 'Eliminar una sede del sistema' },
                { cls: 'view',   text: 'Ver el listado de sedes y su información' },
            ]
        },
        {
            keys: ['group', 'grupo', 'rol', 'role'],
            icon: 'bi-shield-lock-fill', color: '#7c3aed',
            desc: 'Grupos/roles de acceso de Django. Define qué conjunto de permisos tiene cada tipo de usuario (ej: "Cajero", "Directivo").',
            ops: [
                { cls: 'add',    text: 'Crear un nuevo rol con su nombre y permisos' },
                { cls: 'change', text: 'Modificar los permisos asignados a un rol existente' },
                { cls: 'delete', text: 'Eliminar un rol del sistema' },
                { cls: 'view',   text: 'Consultar los roles definidos y sus permisos' },
            ],
            warn: 'Modificar roles afecta a todos los usuarios que los tienen asignados.'
        },
        {
            keys: ['permission', 'permiso'],
            icon: 'bi-toggles', color: '#7c3aed',
            desc: 'Tabla interna de Django con todos los permisos del sistema. Permite asignar permisos individuales directamente a un usuario, sin pasar por un rol.',
            ops: [
                { cls: 'view',   text: 'Ver la lista de permisos disponibles' },
                { cls: 'change', text: 'Asignar o quitar un permiso individual a un usuario' },
            ],
            warn: 'Usar permisos individuales puede eludir la lógica de roles y generar accesos inconsistentes.'
        },
        {
            keys: ['carrera', 'plan', 'programa'],
            icon: 'bi-book-fill', color: '#059669',
            desc: 'Carreras y planes de estudio ofertados por la institución. Los alumnos se inscriben en una carrera.',
            ops: [
                { cls: 'add',    text: 'Crear una nueva carrera o plan de estudio' },
                { cls: 'change', text: 'Modificar nombre, duración o aranceles de la carrera' },
                { cls: 'delete', text: 'Eliminar una carrera del sistema' },
                { cls: 'view',   text: 'Consultar las carreras disponibles' },
            ]
        },
        {
            keys: ['curso', 'clase', 'materia', 'comision', 'comisión'],
            icon: 'bi-calendar3', color: '#0891b2',
            desc: 'Cursos activos, materias y comisiones de cada ciclo lectivo. Cada curso tiene su período, carrera y alumnos inscriptos.',
            ops: [
                { cls: 'add',    text: 'Crear un nuevo curso o comisión' },
                { cls: 'change', text: 'Editar fechas, nombre o capacidad del curso' },
                { cls: 'delete', text: 'Eliminar un curso o comisión' },
                { cls: 'view',   text: 'Ver los cursos activos y sus alumnos' },
            ]
        },
        {
            keys: ['log', 'registro', 'audit', 'logentry', 'log entry'],
            icon: 'bi-journal-text', color: '#6b7280',
            desc: '"Log Entry" es el historial de acciones del panel de administración de Django. Registra automáticamente quién hizo qué y cuándo (crear, editar, eliminar registros).',
            ops: [
                { cls: 'view',   text: 'Consultar el historial de acciones de todos los usuarios' },
                { cls: 'delete', text: 'Borrar entradas del historial de auditoría' },
            ],
            warn: 'Solo otorgar vista a personal de auditoría. Permitir eliminar borra rastros de actividad.'
        },
        {
            keys: ['session', 'sesion'],
            icon: 'bi-clock-history', color: '#dc2626',
            desc: '"Session" es la tabla de sesiones activas de Django. Cada vez que alguien inicia sesión se crea un registro aquí.',
            ops: [
                { cls: 'view',   text: 'Ver qué sesiones están activas en este momento' },
                { cls: 'delete', text: 'Cerrar la sesión de cualquier usuario forzosamente' },
            ],
            warn: 'Permite cerrar sesiones ajenas. No asignar a usuarios sin rol de soporte técnico.'
        },
        {
            keys: ['token'],
            icon: 'bi-key-fill', color: '#dc2626',
            desc: 'Tokens de autenticación para acceso vía API externa (REST). Si tu sistema no usa una API, este módulo no debería tener permisos asignados.',
            ops: [
                { cls: 'add',    text: 'Generar un token de API para un usuario' },
                { cls: 'delete', text: 'Revocar un token y bloquear el acceso de API' },
                { cls: 'view',   text: 'Ver los tokens activos' },
            ],
            warn: 'Un token comprometido permite acceso remoto al sistema. Uso exclusivo de personal técnico.'
        },
        {
            keys: ['content type', 'contenttype', 'tipo de contenido'],
            icon: 'bi-grid-3x3-gap-fill', color: '#6b7280',
            desc: '"Content Type" es una tabla interna de Django que registra todos los modelos del sistema (Alumno, Pago, Usuario, etc.). No se usa directamente en la operación diaria.',
            ops: [
                { cls: 'view', text: 'Ver la lista de tipos de contenido registrados' },
            ],
            warn: 'Tabla de uso interno del framework. No modificar salvo que seas desarrollador.'
        },
        {
            keys: ['inscripcion', 'inscripción', 'enrollment'],
            icon: 'bi-file-earmark-person-fill', color: '#0891b2',
            desc: 'Inscripción de alumnos a carreras o cursos. Vincula un alumno con la comisión en la que cursará.',
            ops: [
                { cls: 'add',    text: 'Inscribir un alumno a una carrera o curso' },
                { cls: 'change', text: 'Modificar la comisión o estado de la inscripción' },
                { cls: 'delete', text: 'Dar de baja una inscripción' },
                { cls: 'view',   text: 'Consultar las inscripciones activas y su historial' },
            ]
        },
        {
            keys: ['cuota', 'fee', 'arancel'],
            icon: 'bi-calendar-check-fill', color: '#d97706',
            desc: 'Cuotas o aranceles que debe pagar cada alumno. Define el monto, la fecha de vencimiento y el estado (pendiente, pagado).',
            ops: [
                { cls: 'add',    text: 'Generar cuotas para un alumno o curso' },
                { cls: 'change', text: 'Modificar montos, vencimiento o estado de una cuota' },
                { cls: 'delete', text: 'Eliminar una cuota pendiente' },
                { cls: 'view',   text: 'Ver las cuotas de cada alumno y su estado' },
            ]
        },
        {
            keys: ['documento', 'document', 'archivo'],
            icon: 'bi-file-earmark-fill', color: '#6b7280',
            desc: 'Documentación adjunta a los legajos: copias de cédula, certificados, comprobantes de pago y archivos varios.',
            ops: [
                { cls: 'add',    text: 'Subir un documento al legajo de un alumno' },
                { cls: 'change', text: 'Reemplazar o actualizar un documento existente' },
                { cls: 'delete', text: 'Eliminar un documento del legajo' },
                { cls: 'view',   text: 'Descargar y consultar documentos adjuntos' },
            ]
        },
    ];

    const HIGH_RISK_KEYS = [
        'user', 'usuario', 'group', 'grupo', 'rol', 'role',
        'permission', 'permiso', 'session', 'sesion',
        'log', 'logentry', 'log entry', 'token',
        'content type', 'contenttype'
    ];

    const ACTION_META = [
        {
            patterns: [/^can add\s+(.+)$/i, /^add\s+(.+)$/i],
            icon: 'bi-plus-lg', cls: 'add', verb: 'Crear',
            descFn: model => `Permite registrar nuevos elementos de tipo "${model}".`
        },
        {
            patterns: [/^can change\s+(.+)$/i, /^change\s+(.+)$/i],
            icon: 'bi-pencil-fill', cls: 'change', verb: 'Editar',
            descFn: model => `Permite modificar registros existentes de "${model}".`
        },
        {
            patterns: [/^can delete\s+(.+)$/i, /^delete\s+(.+)$/i],
            icon: 'bi-trash3-fill', cls: 'delete', verb: 'Eliminar',
            descFn: model => `Permite borrar permanentemente registros de "${model}". ¡Irreversible!`
        },
        {
            patterns: [/^can view\s+(.+)$/i, /^view\s+(.+)$/i],
            icon: 'bi-eye-fill', cls: 'view', verb: 'Ver',
            descFn: model => `Permite listar y consultar registros de "${model}".`
        },
        {
            patterns: [/^puede agregar\s+(.+)$/i, /^puede añadir\s+(.+)$/i, /^agregar\s+(.+)$/i],
            icon: 'bi-plus-lg', cls: 'add', verb: 'Crear',
            descFn: model => `Permite registrar nuevos elementos de tipo "${model}".`
        },
        {
            patterns: [/^puede cambiar\s+(.+)$/i, /^puede modificar\s+(.+)$/i, /^cambiar\s+(.+)$/i],
            icon: 'bi-pencil-fill', cls: 'change', verb: 'Editar',
            descFn: model => `Permite modificar registros existentes de "${model}".`
        },
        {
            patterns: [/^puede eliminar\s+(.+)$/i, /^eliminar\s+(.+)$/i, /^puede borrar\s+(.+)$/i],
            icon: 'bi-trash3-fill', cls: 'delete', verb: 'Eliminar',
            descFn: model => `Permite borrar permanentemente registros de "${model}". ¡Irreversible!`
        },
        {
            patterns: [/^puede ver\s+(.+)$/i, /^ver\s+(.+)$/i, /^puede visualizar\s+(.+)$/i],
            icon: 'bi-eye-fill', cls: 'view', verb: 'Ver',
            descFn: model => `Permite listar y consultar registros de "${model}".`
        },
    ];

    const DANGER_PERM_KEYS = [
        'staff', 'superuser', 'admin', 'log entry', 'session',
        'content type', 'token', 'password'
    ];

    /* Lookup limpio para íconos del popover — FIX del bug de interpolación */
    const OP_ICONS = {
        add:    { icon: 'bi-plus-lg',      cls: 'add'    },
        change: { icon: 'bi-pencil-fill',  cls: 'change' },
        delete: { icon: 'bi-trash3-fill',  cls: 'delete' },
        view:   { icon: 'bi-eye-fill',     cls: 'view'   },
    };

    function parsePermission(name) {
        const trimmed = name.trim();
        for (const action of ACTION_META) {
            for (const pattern of action.patterns) {
                const match = trimmed.match(pattern);
                if (match) {
                    return {
                        icon: action.icon,
                        cls:  action.cls,
                        verb: action.verb,
                        desc: action.descFn(capitalize(match[1]))
                    };
                }
            }
        }
        const isDanger = DANGER_PERM_KEYS.some(k => trimmed.toLowerCase().includes(k));
        return {
            icon: isDanger ? 'bi-exclamation-triangle-fill' : 'bi-gear-fill',
            cls:  isDanger ? 'danger' : 'custom',
            verb: 'Acción',
            desc: isDanger
                ? '⚠ Permiso sensible — puede otorgar acceso privilegiado al sistema.'
                : 'Acción personalizada del sistema. Consultá la documentación para más detalle.'
        };
    }

    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }

    function getModuleMeta(moduleName) {
        const lower = moduleName.toLowerCase();
        for (const meta of MODULE_META) {
            if (meta.keys.some(k => lower.includes(k))) return meta;
        }
        return { icon: 'bi-grid-fill', color: '#64748b', desc: 'Módulo del sistema. Consultá con el administrador para más detalle.', ops: [] };
    }

    function isHighRiskModule(name) {
        const lower = name.toLowerCase();
        return HIGH_RISK_KEYS.some(k => lower.includes(k));
    }

    /*REFS*/
    const busqueda       = $('fr-search');
    const vacioEstado    = $('fr-perms-empty');
    const statModulos    = $('stat-modulos');
    const statTotal      = $('stat-total');
    const statSel        = $('stat-sel');
    const statRiesgo     = $('stat-riesgo');
    const adminNotice    = $('fr-admin-notice');
    const adminPermsList = $('fr-admin-perms-list');
    const expandBtn      = $('fr-expand-all');

    let todoExpandido = true;

    /* ENRICH PERMISSIONS*/
    function enrichPermissions() {
        $$('.fr-perm').forEach(perm => {
            const label = perm.querySelector('label');
            if (!label || label.dataset.enriched) return;

            const originalText = label.textContent.trim();
            const parsed = parsePermission(originalText);

            label.innerHTML = `
                <div class="fr-perm-label-top">
                    <div class="fr-perm-action-icon ${parsed.cls}">
                        <i class="bi ${parsed.icon}"></i>
                    </div>
                    <span class="fr-perm-name">${originalText}</span>
                </div>
                <span class="fr-perm-desc">${parsed.desc}</span>
            `;
            label.dataset.enriched = 'true';

            if (parsed.cls === 'delete' || parsed.cls === 'danger') {
                perm.classList.add('high-risk');
            }
        });
    }

    /*ORDENAR MÓDULOS: sistema primero, Django después*/

const DJANGO_INTERNAL_KEYS = [
    'logentry', 'log entry', 'permission', 'group', 'grupo',
    'session', 'sesion', 'contenttype', 'content type', 'token'
];

function isDjangoInternal(name) {
    const lower = name.toLowerCase();
    return DJANGO_INTERNAL_KEYS.some(k => lower.includes(k));
}

function ordenarModulos() {
    const contenedor = document.querySelector('.fr-body > div:last-child');
    if (!contenedor) return;

    const modulos = $$('.fr-module', contenedor);
    if (!modulos.length) return;

    /* Separar en dos grupos */
    const sistema = modulos.filter(m => !isDjangoInternal(m.dataset.modulo || ''));
    const django  = modulos.filter(m =>  isDjangoInternal(m.dataset.modulo || ''));

    /* Si hay módulos Django, agregar separador visual antes de ellos */
    if (django.length) {
        const sep = document.createElement('div');
        sep.className = 'fr-section-sep';
        sep.innerHTML = `
            <div class="fr-section-sep-line"></div>
            <span class="fr-section-sep-label">
                <i class="bi bi-gear-fill"></i> Módulos internos de Django
            </span>
            <div class="fr-section-sep-line"></div>
        `;

        /* Reordenar en el DOM */
        sistema.forEach(m => contenedor.appendChild(m));
        contenedor.appendChild(sep);
        django.forEach(m => contenedor.appendChild(m));
    }
}

    /*ENRICH MODULES*/
    function enhanceModules() {
        $$('.fr-module').forEach(mod => {
            const nombre   = mod.dataset.modulo || '';
            const meta     = getModuleMeta(nombre);
            const esRiesgo = isHighRiskModule(nombre);

            const iconEl = mod.querySelector('.fr-module-icon');
            if (iconEl) {
                iconEl.innerHTML = `<i class="bi ${meta.icon}"></i>`;
                iconEl.style.cssText = `
                    background: ${meta.color}18;
                    color: ${meta.color};
                    border-color: ${meta.color}30;
                `;
            }

            const nameEl = mod.querySelector('.fr-module-name');
            if (nameEl && !nameEl.closest('.fr-module-title-wrap')) {
                const wrap = document.createElement('div');
                wrap.className = 'fr-module-title-wrap';

                const newName = document.createElement('span');
                newName.className = 'fr-module-name';
                newName.textContent = nameEl.textContent;

                const descEl = document.createElement('span');
                descEl.className = 'fr-module-desc';
                descEl.textContent = meta.desc;

                wrap.appendChild(newName);
                wrap.appendChild(descEl);
                nameEl.replaceWith(wrap);
            }

            if (esRiesgo) {
                mod.classList.add('risk-high');
                const right = mod.querySelector('.fr-module-right');
                if (right && !mod.querySelector('.fr-risk-label')) {
                    const tag = document.createElement('span');
                    tag.className = 'fr-risk-label';
                    tag.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> Riesgo';
                    right.insertBefore(tag, right.firstChild);
                }
            }
        });
    }

    /*COLAPSAR / EXPANDIR (individual)*/
    function alternarModulo(modulo) {
        const estaAbierto = modulo.classList.contains('abierto');
        const cab         = modulo.querySelector('.fr-module-head');
        const bodyId      = cab ? cab.getAttribute('aria-controls') : null;
        const body        = bodyId ? $(bodyId) : null;

        if (estaAbierto) {
            modulo.classList.remove('abierto');
            if (cab)  cab.setAttribute('aria-expanded', 'false');
            if (body) body.classList.add('oculto');
        } else {
            modulo.classList.add('abierto');
            if (cab)  cab.setAttribute('aria-expanded', 'true');
            if (body) body.classList.remove('oculto');
        }
    }

    $$('.fr-module-head').forEach(cab => {
        cab.addEventListener('click', function (e) {
            if (e.target.closest('.fr-sel-all'))   return;
            if (e.target.closest('.fr-risk-label')) return;
            if (e.target.closest('.fr-info-btn'))   return;
            alternarModulo(this.closest('.fr-module'));
        });

        cab.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                alternarModulo(this.closest('.fr-module'));
            }
        });
    });

    /*EXPANDIR / COLAPSAR*/
    if (expandBtn) {
        expandBtn.addEventListener('click', () => {
            todoExpandido = !todoExpandido;
            $$('.fr-module').forEach(mod => {
                const cab    = mod.querySelector('.fr-module-head');
                const bodyId = cab ? cab.getAttribute('aria-controls') : null;
                const body   = bodyId ? $(bodyId) : null;

                mod.classList.toggle('abierto', todoExpandido);
                if (cab)  cab.setAttribute('aria-expanded', String(todoExpandido));
                if (body) body.classList.toggle('oculto', !todoExpandido);
            });
            expandBtn.innerHTML = todoExpandido
                ? '<i class="bi bi-arrows-collapse"></i> Colapsar todo'
                : '<i class="bi bi-arrows-expand"></i> Expandir todo';
        });
    }

    /*STATS*/
    function actualizarStats() {
        const todos    = $$('.fr-perm input[type="checkbox"]');
        const marcados = todos.filter(c => c.checked);
        const riesgo   = marcados.filter(c => c.closest('.fr-perm.high-risk'));

        if (statTotal)   statTotal.textContent   = todos.length;
        if (statSel)     statSel.textContent      = marcados.length;
        if (statModulos) statModulos.textContent  = $$('.fr-module').length;
        if (statRiesgo)  statRiesgo.textContent   = riesgo.length;

        actualizarAdminNotice(riesgo);
    }

    function actualizarAdminNotice(riesgoChecks) {
        if (!adminNotice) return;
        adminNotice.classList.toggle('visible', riesgoChecks.length > 0);
        if (!adminPermsList) return;
        adminPermsList.innerHTML = '';
        riesgoChecks.slice(0, 8).forEach(chk => {
            const labelEl  = document.querySelector(`label[for="${chk.id}"]`);
            const nameSpan = labelEl ? labelEl.querySelector('.fr-perm-name') : null;
            const texto    = nameSpan
                ? nameSpan.textContent.trim()
                : (labelEl ? labelEl.textContent.replace(/\s+/g, ' ').trim() : chk.value);
            const tag = document.createElement('span');
            tag.className = 'fr-admin-perm-tag';
            tag.innerHTML = `<i class="bi bi-exclamation-circle"></i> ${texto}`;
            adminPermsList.appendChild(tag);
        });
        if (riesgoChecks.length > 8) {
            const more = document.createElement('span');
            more.className = 'fr-admin-perm-tag';
            more.textContent = `+${riesgoChecks.length - 8} más`;
            adminPermsList.appendChild(more);
        }
    }

    /*BADGE POR MÓDULO*/
    function actualizarBadge(modulo) {
        const chks     = $$('input[type="checkbox"]', modulo);
        const marcados = chks.filter(c => c.checked).length;
        const badge    = modulo.querySelector('.fr-module-badge');
        if (!badge) return;
        badge.textContent = `${marcados} / ${chks.length}`;
        badge.classList.toggle('activo', marcados > 0);
    }

    /*SELECCIONAR MÓDULO*/
    $$('.fr-sel-all').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            const body  = $(btn.dataset.destino);
            const chks  = $$('input[type="checkbox"]', body);
            const todos = chks.every(c => c.checked);
            chks.forEach(c => c.checked = !todos);
            btn.innerHTML = todos
                ? '<i class="bi bi-check2-all"></i> Todos'
                : '<i class="bi bi-x-circle"></i> Ninguno';
            actualizarBadge(btn.closest('.fr-module'));
            actualizarStats();
        });
    });

    /*CHANGE INDIVIDUAL*/
    $$('.fr-perm input[type="checkbox"]').forEach(chk => {
        chk.addEventListener('change', () => {
            actualizarBadge(chk.closest('.fr-module'));
            actualizarStats();
        });
    });

    /*BÚSQUEDA*/
    if (busqueda) {
        busqueda.addEventListener('input', function () {
            const termino = this.value.trim().toLowerCase();
            let hayVisible = false;

            $$('.fr-module').forEach(mod => {
                const perms = $$('.fr-perm', mod);
                let moduloVisible = false;

                perms.forEach(perm => {
                    const etiqueta = perm.dataset.etiqueta || '';
                    const descEl   = perm.querySelector('.fr-perm-desc');
                    const desc     = descEl ? descEl.textContent.toLowerCase() : '';
                    const coincide = !termino || etiqueta.includes(termino) || desc.includes(termino);
                    perm.classList.toggle('oculto', !coincide);
                    if (coincide) moduloVisible = true;
                });

                mod.style.display = moduloVisible ? '' : 'none';
                if (moduloVisible) hayVisible = true;

                if (termino && moduloVisible) {
                    const cab    = mod.querySelector('.fr-module-head');
                    const bodyId = cab ? cab.getAttribute('aria-controls') : null;
                    const body   = bodyId ? $(bodyId) : null;
                    mod.classList.add('abierto');
                    if (cab)  cab.setAttribute('aria-expanded', 'true');
                    if (body) body.classList.remove('oculto');
                }
            });

            if (vacioEstado) vacioEstado.style.display = hayVisible ? 'none' : 'block';
        });
    }

    /*APLICAR fr-input A WIDGETS DE DJANGO*/
    document.querySelectorAll(
        '.fr input:not([type=checkbox]):not([type=hidden]),.fr select,.fr textarea'
    ).forEach(el => el.classList.add('fr-input'));

    /*BOTÓN ⓘ Y POPOVER*/
    function initInfoButtons() {
        const pop = document.createElement('div');
        pop.className = 'fr-popover';
        pop.setAttribute('role', 'tooltip');
        document.body.appendChild(pop);

        let btnActivo = null;

        function cerrarPopover() {
            pop.classList.remove('visible');
            if (btnActivo) btnActivo.classList.remove('activo');
            btnActivo = null;
        }

        function abrirPopover(btn, meta, codename, nombreVisible) {
            const opsHtml = (meta.ops || []).map(op => {
                const { icon, cls } = OP_ICONS[op.cls] || OP_ICONS.view;
                return `
                    <div class="fr-popover-op">
                        <i class="bi ${icon} ${cls}"></i>
                        <span>${op.text}</span>
                    </div>
                `;
            }).join('');

            const warnHtml = meta.warn
                ? `<div class="fr-popover-warn">⚠ ${meta.warn}</div>`
                : '';

            pop.innerHTML = `
                <div class="fr-popover-head">
                    <div class="fr-popover-icon" style="background:${meta.color}18;color:${meta.color}">
                        <i class="bi ${meta.icon}"></i>
                    </div>
                    <div>
                        <div class="fr-popover-title">${nombreVisible}</div>
                        <div class="fr-popover-codename">${codename}</div>
                    </div>
                </div>
                <div class="fr-popover-body">
                    <p class="fr-popover-desc">${meta.desc}</p>
                    ${opsHtml ? `<div class="fr-popover-ops">${opsHtml}</div>` : ''}
                    ${warnHtml}
                </div>
            `;

            const rect       = btn.getBoundingClientRect();
            const spaceAbajo = window.innerHeight - rect.bottom;
            const spaceArriba = rect.top;
            const usarArriba  = spaceAbajo < 320 && spaceArriba > spaceAbajo;

            pop.classList.remove('arriba', 'abajo');
            pop.classList.add(usarArriba ? 'arriba' : 'abajo');

            pop.style.visibility = 'hidden';
            pop.style.display    = 'block';
            const popH = pop.offsetHeight;
            pop.style.display    = '';
            pop.style.visibility = '';

            const top = usarArriba
                ? rect.top  - popH - 8
                : rect.bottom + 8;

            let left = rect.left - 8;
            left = Math.min(left, window.innerWidth - 288 - 8);
            left = Math.max(left, 8);

            pop.style.top  = top  + 'px';
            pop.style.left = left + 'px';

            pop.classList.add('visible');
            btn.classList.add('activo');
            btnActivo = btn;
        }

        $$('.fr-module').forEach(mod => {
            const cab   = mod.querySelector('.fr-module-head');
            const right = mod.querySelector('.fr-module-right');
            if (!cab || !right) return;

            const codename      = (mod.dataset.modulo || '').trim();
            const nombreEl      = mod.querySelector('.fr-module-title-wrap .fr-module-name')
                || mod.querySelector('.fr-module-name');
            const nombreVisible = nombreEl ? nombreEl.textContent.trim() : codename;
            const meta          = getModuleMeta(codename);

            const btn = document.createElement('button');
            btn.type      = 'button';
            btn.className = 'fr-info-btn';
            btn.title     = `¿Qué es ${nombreVisible || codename}?`;
            btn.innerHTML = '<i class="bi bi-info-lg"></i>';
            btn.setAttribute('aria-label', `Información sobre el módulo ${nombreVisible}`);

            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                if (btnActivo === btn) {
                    cerrarPopover();
                    return;
                }
                cerrarPopover();
                abrirPopover(btn, meta, codename, nombreVisible);
            });

            const badge = right.querySelector('.fr-module-badge');
            if (badge) right.insertBefore(btn, badge);
            else       right.insertBefore(btn, right.firstChild);
        });

        document.addEventListener('click', function (e) {
            if (!pop.contains(e.target)) cerrarPopover();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') cerrarPopover();
        });

        window.addEventListener('scroll', cerrarPopover, { passive: true });
        window.addEventListener('resize', cerrarPopover, { passive: true });
    }

    /*INIT*/
    ordenarModulos();
    enhanceModules();
    enrichPermissions();
    initInfoButtons();
    $$('.fr-module').forEach(actualizarBadge);
    actualizarStats();

})();