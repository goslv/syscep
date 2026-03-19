
/* ── ThemeManager ─────────────────────────────────── */
class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('themeToggle');
        this.html = document.documentElement;
        this.init();
    }

    init() {
        const savedTheme  = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme       = savedTheme || (prefersDark ? 'dark' : 'light');

        this.setTheme(theme);

        if (this.themeToggle) {
            this.updateToggleIcon(theme);
            this.themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    setTheme(theme) {
        this.html.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (this.themeToggle) this.updateToggleIcon(theme);
        document.dispatchEvent(new CustomEvent('themeChange', { detail: { theme } }));
    }

    toggleTheme() {
        const current = this.html.getAttribute('data-theme');
        this.setTheme(current === 'dark' ? 'light' : 'dark');
    }

    updateToggleIcon(theme) {
        const icon = this.themeToggle.querySelector('i');
        if (!icon) return;
        icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        this.themeToggle.classList.add('animate-spin-once');
        setTimeout(() => this.themeToggle.classList.remove('animate-spin-once'), 500);
    }
}

/* ── SidebarManager ───────────────────────────────── */
class SidebarManager {
    constructor() {
        this.sidebar        = document.getElementById('sidebar');
        this.overlay        = document.getElementById('sidebarOverlay');
        this.menuToggle     = document.getElementById('menuToggle');
        this.toggleBtn      = document.getElementById('sidebarToggleBtn');   // botón desktop
        this.mainContent    = document.getElementById('main-content');
        this.body           = document.body;
        this.isMobile       = window.innerWidth <= 1024;

        this.init();
    }

    init() {
        this.setInitialState();
        this.bindEvents();
        this.detectResize();
    }

    bindEvents() {
        // Botón hamburguesa (móvil)
        this.menuToggle?.addEventListener('click', () => this.toggle());

        // Botón toggle dentro del sidebar (desktop)
        this.toggleBtn?.addEventListener('click', () => this.toggle());

        // Cerrar al hacer clic en el overlay
        this.overlay?.addEventListener('click', () => this.closeMobile());

        // Cerrar al navegar en móvil
        this.sidebar?.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (this.isMobile) this.closeMobile();
            });
        });
    }

    toggle() {
        if (this.isMobile) {
            // Móvil: mostrar/ocultar el sidebar deslizante
            const isOpen = this.sidebar.classList.toggle('show');
            this.overlay.classList.toggle('show', isOpen);
            this.body.style.overflow = isOpen ? 'hidden' : '';
            this.menuToggle?.setAttribute('aria-expanded', isOpen);
        } else {
            // Desktop: colapsar/expandir con animación de padding en top-bar
            const isCollapsing = !this.sidebar.classList.contains('collapsed');
            this.sidebar.classList.toggle('collapsed', isCollapsing);
            this.mainContent?.classList.toggle('sidebar-collapsed', isCollapsing);
            localStorage.setItem('sidebarCollapsed', isCollapsing);
        }
    }

    closeMobile() {
        this.sidebar?.classList.remove('show');
        this.overlay?.classList.remove('show');
        this.body.style.overflow = '';
        this.menuToggle?.setAttribute('aria-expanded', 'false');
    }

    setInitialState() {
        // Restaurar estado colapsado en desktop
        if (!this.isMobile && localStorage.getItem('sidebarCollapsed') === 'true') {
            this.sidebar?.classList.add('collapsed');
            this.mainContent?.classList.add('sidebar-collapsed');
        }
    }

    detectResize() {
        const checkMobile = () => {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 1024;

            // Al pasar de móvil a desktop, limpiar estado móvil
            if (wasMobile && !this.isMobile) {
                this.closeMobile();
                // Restaurar collapsed si corresponde
                if (localStorage.getItem('sidebarCollapsed') === 'true') {
                    this.sidebar?.classList.add('collapsed');
                    this.mainContent?.classList.add('sidebar-collapsed');
                }
            }
        };

        window.addEventListener('resize', checkMobile);
    }
}

/* ── DropdownManager ──────────────────────────────── */
class DropdownManager {
    constructor() {
        this.dropdowns = new Map();
        this.init();
    }

    init() {
        // Dropdowns genéricos con data-attributes
        document.querySelectorAll('[data-dropdown]').forEach(dropdown => {
            const toggle = dropdown.querySelector('[data-dropdown-toggle]');
            const menu   = dropdown.querySelector('[data-dropdown-menu]');
            if (toggle && menu) {
                this.dropdowns.set(dropdown, { toggle, menu, open: false });
                this.bindDropdownEvents(dropdown);
            }
        });

        // Dropdown del usuario
        const userToggle = document.getElementById('userDropdownToggle');
        const userMenu   = document.getElementById('userDropdownMenu');

        if (userToggle && userMenu) {
            userToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                // Cerrar panel de notificaciones si está abierto
                window.app?.notifications?.close();

                const isShowing = userMenu.classList.toggle('show');
                userToggle.setAttribute('aria-expanded', isShowing);
            });
        }

        // Cerrar al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (userMenu && userToggle && !userToggle.contains(e.target) && !userMenu.contains(e.target)) {
                userMenu.classList.remove('show');
                userToggle?.setAttribute('aria-expanded', 'false');
            }

            this.dropdowns.forEach((data, dropdown) => {
                if (!dropdown.contains(e.target) && data.open) this.closeDropdown(dropdown);
            });
        });

        // Cerrar con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Escape') return;
            userMenu?.classList.remove('show');
            userToggle?.setAttribute('aria-expanded', 'false');
            this.dropdowns.forEach((data, dropdown) => {
                if (data.open) this.closeDropdown(dropdown);
            });
        });
    }

    bindDropdownEvents(dropdown) {
        const { toggle } = this.dropdowns.get(dropdown);
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown(dropdown);
        });
    }

    toggleDropdown(dropdown) {
        const data = this.dropdowns.get(dropdown);
        data.open ? this.closeDropdown(dropdown) : this.openDropdown(dropdown);
    }

    openDropdown(dropdown) {
        const data = this.dropdowns.get(dropdown);
        data.menu.classList.add('show');
        data.open = true;
    }

    closeDropdown(dropdown) {
        const data = this.dropdowns.get(dropdown);
        data.menu.classList.remove('show');
        data.open = false;
    }
}

/* ── SearchManager ────────────────────────────────── */
class SearchManager {
    constructor() {
        this.searchInput      = document.getElementById('globalSearch');
        this.searchContainer  = document.getElementById('globalSearchContainer');
        this.resultsContainer = document.getElementById('searchResults');
        this.searchToggle     = document.getElementById('searchToggleMobile');
        this.closeBtn         = document.getElementById('closeSearchMobile');
        this.init();
    }

    init() {
        if (!this.searchInput) return;

        // Toggle móvil
        this.searchToggle?.addEventListener('click', () => {
            this.searchContainer?.classList.add('show-mobile');
            this.searchInput.focus();
        });

        this.closeBtn?.addEventListener('click', () => {
            this.searchContainer?.classList.remove('show-mobile');
            this.searchInput.value = '';
            this.hideResults();
        });

        // Enviar búsqueda con Enter (si no hay resultados seleccionados)
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = this.searchInput.value.trim();
                // Si hay resultados visibles, podríamos navegar al primero, 
                // pero por ahora mantengamos la redirección a alumnos como fallback
                if (query && !this.resultsContainer.querySelector('.search-result-item')) {
                    window.location.href = `/alumnos/?busqueda=${encodeURIComponent(query)}`;
                }
            }
        });

        // Búsqueda en tiempo real (debounced)
        this.searchInput.addEventListener('input', this.debounce((e) => {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                this.performSearch(query);
            } else {
                this.hideResults();
            }
        }, 300));

        // Cerrar resultados al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!this.searchContainer.contains(e.target)) {
                this.hideResults();
            }
        });

        // Atajo de teclado Ctrl+K
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.searchInput.focus();
            }

            if (e.key === 'Escape') {
                this.searchContainer?.classList.remove('show-mobile');
                this.searchInput.blur();
                this.hideResults();
            }
        });

        // Placeholder dinámico
        this.searchInput.addEventListener('focus', () => {
            this.searchInput.setAttribute('placeholder', 'Presiona Ctrl+K para buscar rápidamente...');
            if (this.searchInput.value.trim().length >= 2) {
                this.showResults();
            }
        });
        this.searchInput.addEventListener('blur', () => {
            this.searchInput.setAttribute('placeholder', 'Buscar alumnos, pagos, carreras...');
        });
    }

    async performSearch(query) {
        try {
            const response = await fetch(`/buscar-global/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.renderResults(data.resultados);
        } catch (error) {
            console.error('Error en búsqueda global:', error);
        }
    }

    renderResults(resultados) {
        if (!this.resultsContainer) return;

        // Mapa de íconos de fallback por tipo
        const iconMap = {
            'ALUMNO':      'bi-person-fill',
            'PAGO':        'bi-cash-stack',
            'CARRERA':     'bi-mortarboard-fill',
            'FUNCIONARIO': 'bi-person-badge-fill',
            'SEDE':        'bi-building',
            'USUARIO':     'bi-person-lock',
        };

        if (resultados.length === 0) {
            this.resultsContainer.innerHTML = `
            <div class="search-no-results">
                <i class="bi bi-search mb-2 d-block" style="font-size: 1.5rem; opacity: 0.3;"></i>
                No se encontraron coincidencias para tu búsqueda.
            </div>
        `;
        } else {
            this.resultsContainer.innerHTML = resultados.map(res => {
                // Fallback: usa el mapa por tipo si no hay ícono
                const icon = res.icon || iconMap[res.tipo?.toUpperCase()] || 'bi-search';
                return `
                <a href="${res.url}" class="search-result-item">
                    <div class="search-result-icon">
                        <i class="bi ${icon}"></i>
                    </div>
                    <div class="search-result-content">
                        <span class="search-result-title">${this.highlightMatch(res.titulo)}</span>
                        <span class="search-result-sub">${res.subtitulo}</span>
                    </div>
                    <span class="search-result-type">${res.tipo}</span>
                </a>
            `;
            }).join('');
        }

        this.showResults();
    }

    highlightMatch(text) {
        const query = this.searchInput.value.trim();
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    showResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'block';
        }
    }

    hideResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'none';
        }
    }

    debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    }
}

/* ── NotificationManager ──────────────────────────── */
class NotificationManager {
    constructor() {
        this.toggleButton = document.getElementById('notificationsToggle');
        this.panel        = document.getElementById('notificationPanel');
        this.list         = document.getElementById('notificationList');
        this.count        = document.getElementById('notificationCount');
        this.clearButton  = document.getElementById('notificationsClear');
        this.dot          = this.toggleButton?.querySelector('.notification-dot');
        this.isOpen       = false;

        this.init();
    }

    init() {
        if (!this.toggleButton || !this.panel || !this.list) return;

        // Modales Bootstrap
        this.modalDetalle  = new bootstrap.Modal(document.getElementById('modalDetalleNotif'));
        this.modalHistorial = new bootstrap.Modal(document.getElementById('modalHistorialNotif'));
        this.historialList  = document.getElementById('historialList');
        this.btnHistorial   = document.getElementById('btnHistorialNotif');
        this.btnClearHistorial = document.getElementById('btnClearHistorial');

        // Filtrar notificaciones ya leídas
        this.checkPersistedNotifications();
        this.renderNotifications();

        // Eventos
        this.toggleButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggle();
        });

        this.panel.addEventListener('click', (e) => e.stopPropagation());

        this.clearButton?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.markAllRead();
        });

        this.btnHistorial?.addEventListener('click', () => {
            this.close();
            this.showHistory();
        });

        this.btnClearHistorial?.addEventListener('click', () => {
            if (confirm('¿Estás seguro de que deseas borrar todo el historial de notificaciones?')) {
                localStorage.removeItem('notifHistory');
                this.renderHistory();
            }
        });

        document.addEventListener('click', () => this.close());
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape') this.close(); });
    }

    handleClick(element) {
        const isSolicitud = element.getAttribute('data-es-solicitud') === 'true';
        if (isSolicitud) {
            this.showDetail(element);
        } else {
            const url = element.getAttribute('data-url');
            this.markRead(element);
            if (url) setTimeout(() => { window.location.href = url; }, 300);
        }
    }

    showDetail(element, isFromHistory = false) {
        const title    = element.getAttribute('data-type');
        const materia  = element.getAttribute('data-materia');
        const carrera  = element.getAttribute('data-carrera');
        const fecha    = element.getAttribute('data-fecha');
        const isSolicitud = element.getAttribute('data-es-solicitud') === 'true';

        const titleEl  = document.getElementById('notifTitle');
        const bodyEl   = document.getElementById('notifBody');
        const footerEl = document.getElementById('notifFooter');

        titleEl.textContent = title;

        let html = `
            <div class="mb-3">
                <div class="d-flex align-items-center mb-2">
                    <div class="rounded-circle bg-light p-2 me-2">
                        <i class="bi ${element.getAttribute('data-icon')} ${element.getAttribute('data-color')}"></i>
                    </div>
                    <div>
                        <h6 class="mb-0 fw-bold">${materia}</h6>
                        <small class="text-muted">${carrera}</small>
                    </div>
                </div>
                <div class="small text-muted mb-3">
                    <i class="bi bi-clock me-1"></i> ${fecha}
                </div>
            </div>`;

        if (isSolicitud) {
            const motivo     = element.getAttribute('data-motivo');
            const urlProcesar = element.getAttribute('data-url-procesar');
            let datos = {};
            if (isFromHistory) {
                try { datos = JSON.parse(element.getAttribute('data-datos-objeto')); } catch (e) {}
            } else {
                const rawData = element.querySelector('script[id="temp"]')?.textContent;
                try { if (rawData) datos = JSON.parse(rawData); } catch (e) {}
            }

            html += `
                <div class="mb-3">
                    <label class="small fw-bold text-muted text-uppercase">Motivo</label>
                    <p class="mb-0 p-3 bg-light rounded border">${motivo}</p>
                </div>
                <div class="mb-3">
                    <label class="small fw-bold text-muted text-uppercase">Datos del Objeto</label>
                    <div class="p-3 bg-light rounded border small">
                        <ul class="list-unstyled mb-0">
                            ${Object.entries(datos).map(([k, v]) =>
                `<li><strong>${k.charAt(0).toUpperCase() + k.slice(1)}:</strong> ${v}</li>`
            ).join('')}
                        </ul>
                    </div>
                </div>
                <form action="${urlProcesar}" method="post" id="formProcesarNotif">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${this.getCookie('csrftoken')}">
                    <div class="mb-3">
                        <label class="form-label small fw-bold text-muted text-uppercase">Observaciones (Opcional)</label>
                        <textarea name="observaciones" class="form-control" rows="2"></textarea>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" name="accion" value="APROBAR" class="btn btn-danger rounded-pill">
                            <i class="bi bi-check-circle me-1"></i> Aprobar y Eliminar
                        </button>
                        <button type="submit" name="accion" value="RECHAZAR" class="btn btn-outline-secondary rounded-pill">
                            <i class="bi bi-x-circle me-1"></i> Rechazar
                        </button>
                    </div>
                </form>`;
            footerEl.style.display = 'none';
        } else {
            html += `<p>Notificación de sistema sobre el examen de ${materia}.</p>`;
            footerEl.style.display = 'flex';
        }

        bodyEl.innerHTML = html;
        this.modalDetalle.show();
        if (!isFromHistory) this.markRead(element);
    }

    showHistory() {
        this.renderHistory();
        this.modalHistorial.show();
    }

    renderHistory() {
        const history = JSON.parse(localStorage.getItem('notifHistory') || '[]');
        if (history.length === 0) {
            this.historialList.innerHTML = `
                <div class="p-5 text-center text-muted">
                    <i class="bi bi-clock-history mb-3 d-block" style="font-size: 3rem; opacity: 0.2;"></i>
                    <p>No hay notificaciones anteriores guardadas</p>
                </div>`;
            this.btnClearHistorial.style.display = 'none';
            return;
        }

        this.btnClearHistorial.style.display = 'block';
        this.historialList.innerHTML = [...history].reverse().map(n => `
            <div class="list-group-item p-3 border-start-0 border-end-0"
                 data-type="${n.type}"
                 data-materia="${n.materia}"
                 data-carrera="${n.carrera}"
                 data-fecha="${n.date}"
                 data-icon="${n.icon}"
                 data-color="${n.color}"
                 data-url="${n.url || ''}"
                 data-es-solicitud="${n.es_solicitud || 'false'}"
                 data-motivo="${n.motivo || ''}"
                 data-url-procesar="${n.url_procesar || ''}"
                 data-solicitud-id="${n.solicitud_id || ''}"
                 data-datos-objeto='${JSON.stringify(n.datos_objeto || {})}'
                 onclick="window.notificationManager.handleHistoryClick(this)"
                 style="cursor:pointer;">
                <div class="d-flex">
                    <div class="me-3">
                        <div class="rounded-circle bg-light p-2">
                            <i class="bi ${n.icon} ${n.color}"></i>
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between">
                            <h6 class="mb-0 fw-bold">${n.type}</h6>
                            <small class="text-muted">${n.date}</small>
                        </div>
                        <div class="small text-muted mt-1">${n.materia} - ${n.carrera}</div>
                        <div class="mt-2">
                            <span class="badge bg-light text-dark border small" style="font-size: 0.7rem;">Ver de nuevo</span>
                        </div>
                    </div>
                </div>
            </div>`).join('');
    }

    handleHistoryClick(element) {
        const isSolicitud = element.getAttribute('data-es-solicitud') === 'true';
        this.modalHistorial.hide();
        if (isSolicitud) {
            this.showDetail(element, true);
        } else {
            const url = element.getAttribute('data-url');
            if (url) window.location.href = url;
        }
    }

    getCookie(name) {
        let value = null;
        if (document.cookie) {
            document.cookie.split(';').forEach(c => {
                const trimmed = c.trim();
                if (trimmed.startsWith(name + '=')) {
                    value = decodeURIComponent(trimmed.substring(name.length + 1));
                }
            });
        }
        return value;
    }

    renderNotifications() {
        const items = this.list.querySelectorAll('.notification-item');
        const count = items.length;

        if (count === 0) {
            if (!this.list.querySelector('.notification-empty')) {
                this.list.innerHTML = `
                    <div class="notification-empty" id="notificationEmpty">
                        <i class="bi bi-bell-slash mb-2" style="font-size: 2rem; opacity: 0.3;"></i>
                        <p class="mb-0">No hay notificaciones nuevas</p>
                    </div>`;
            }
            if (this.dot) this.dot.style.display = 'none';
            if (this.count) { this.count.textContent = '0'; this.count.classList.add('d-none'); }
            return;
        }

        if (this.count) { this.count.textContent = count; this.count.classList.remove('d-none'); }
        if (this.dot)   this.dot.style.display = 'block';
    }

    toggle() { this.isOpen ? this.close() : this.open(); }

    open() {
        // Cerrar el dropdown de usuario si está abierto
        const userMenu   = document.getElementById('userDropdownMenu');
        const userToggle = document.getElementById('userDropdownToggle');
        userMenu?.classList.remove('show');
        userToggle?.setAttribute('aria-expanded', 'false');

        this.panel.classList.add('show');
        this.toggleButton.setAttribute('aria-expanded', 'true');
        this.toggleButton.classList.add('active');
        this.isOpen = true;

        if (this.dot) this.dot.style.display = 'none';
    }

    close() {
        if (!this.isOpen) return;
        this.panel.classList.remove('show');
        this.toggleButton.setAttribute('aria-expanded', 'false');
        this.toggleButton.classList.remove('active');
        this.isOpen = false;
    }

    markRead(element) {
        if (!element?.classList.contains('notification-item')) return;
        element.classList.remove('unread');
        element.classList.add('is-read');
        this.persistReadState(element);

        element.style.transition = 'all 0.3s ease';
        element.style.opacity    = '0';
        element.style.transform  = 'translateX(20px)';

        setTimeout(() => {
            element.remove();
            this.renderNotifications();
        }, 300);
    }

    markAllRead() {
        this.list.querySelectorAll('.notification-item').forEach(item => {
            item.classList.add('fade-out');
            this.persistReadState(item);
        });
        setTimeout(() => {
            this.list.querySelectorAll('.notification-item').forEach(el => el.remove());
            this.renderNotifications();
        }, 300);
    }

    persistReadState(element) {
        const type        = element.getAttribute('data-type');
        const materia     = element.getAttribute('data-materia');
        const carrera     = element.getAttribute('data-carrera');
        const date        = element.getAttribute('data-fecha');
        const icon        = element.getAttribute('data-icon');
        const color       = element.getAttribute('data-color');
        const url         = element.getAttribute('data-url');
        const esSolicitud = element.getAttribute('data-es-solicitud') === 'true';
        const motivo      = element.getAttribute('data-motivo');
        const urlProcesar = element.getAttribute('data-url-procesar');
        const solicitudId = element.getAttribute('data-solicitud-id');

        let datosObjeto = {};
        if (esSolicitud) {
            const raw = element.querySelector('script[id="temp"]')?.textContent;
            try { if (raw) datosObjeto = JSON.parse(raw); } catch (e) {}
        }

        if (!type || !materia || !date) return;

        const id = btoa(`${type}-${materia}-${date}`);

        // Guardar IDs leídos
        let read = JSON.parse(localStorage.getItem('readNotifications') || '[]');
        if (!read.includes(id)) {
            read.push(id);
            if (read.length > 100) read.shift();
            localStorage.setItem('readNotifications', JSON.stringify(read));
        }

        // Guardar en historial
        let history = JSON.parse(localStorage.getItem('notifHistory') || '[]');
        if (!history.find(n => n.id === id)) {
            history.push({ id, type, materia, carrera, date, icon, color, url,
                es_solicitud: esSolicitud, motivo,
                url_procesar: urlProcesar, solicitud_id: solicitudId,
                datos_objeto: datosObjeto });
            if (history.length > 50) history.shift();
            localStorage.setItem('notifHistory', JSON.stringify(history));
        }
    }

    checkPersistedNotifications() {
        const read  = JSON.parse(localStorage.getItem('readNotifications') || '[]');
        const items = this.list.querySelectorAll('.notification-item');
        let removed = 0;

        items.forEach(item => {
            const type    = item.getAttribute('data-type');
            const materia = item.getAttribute('data-materia');
            const date    = item.getAttribute('data-fecha');
            if (type && materia && date) {
                const id = btoa(`${type}-${materia}-${date}`);
                if (read.includes(id)) { item.remove(); removed++; }
            }
        });

        if (removed > 0) this.renderNotifications();
    }
}

/* ── AlertManager ─────────────────────────────────── */
class AlertManager {
    constructor() {
        this.init();
    }

    init() {
        document.querySelectorAll('.alert-auto-close').forEach(alert => {
            setTimeout(() => {
                bootstrap.Alert.getOrCreateInstance(alert)?.close();
            }, 5000);
        });

        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('alert-close-all')) {
                document.querySelectorAll('.alert-custom').forEach(alert => {
                    bootstrap.Alert.getOrCreateInstance(alert)?.close();
                });
            }
        });
    }

    static showAlert(type, message, title = null) {
        const map = {
            success: { icon: 'bi-check-lg',      defaultTitle: '¡Éxito!' },
            warning: { icon: 'bi-exclamation-lg', defaultTitle: 'Advertencia' },
            danger:  { icon: 'bi-x-lg',           defaultTitle: 'Error' },
            info:    { icon: 'bi-info-lg',         defaultTitle: 'Información' },
        };
        const cfg = map[type] || map.info;
        const alertTitle = title || cfg.defaultTitle;

        const html = `
            <div class="alert-custom alert-${type} alert-dismissible fade show alert-auto-close" role="alert">
                <div class="alert-icon"><i class="bi ${cfg.icon}"></i></div>
                <div class="alert-content">
                    <div class="alert-title">${alertTitle}</div>
                    ${message}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
            </div>`;

        const container = document.querySelector('.content-wrapper');
        if (container) container.insertAdjacentHTML('afterbegin', html);

        setTimeout(() => {
            const alert = document.querySelector('.alert-auto-close');
            if (alert) bootstrap.Alert.getOrCreateInstance(alert)?.close();
        }, 5000);
    }
}

/* ── PasswordModalManager ─────────────────────────── */
class PasswordModalManager {
    constructor() {
        this.btnToggle  = document.getElementById('modalBtnTogglePassword');
        this.btnCancel  = document.getElementById('modalBtnCancelPassword');
        this.container  = document.getElementById('modalPasswordFormContainer');
        this.header     = document.getElementById('modalPasswordSectionHeader');
        this.init();
    }

    init() {
        if (!this.btnToggle || !this.btnCancel || !this.container || !this.header) return;

        this.btnToggle.addEventListener('click', () => {
            this.container.classList.remove('d-none');
            this.header.classList.add('d-none');
        });

        this.btnCancel.addEventListener('click', () => {
            this.container.classList.add('d-none');
            this.header.classList.remove('d-none');
        });

        // Limpiar el formulario al cerrar el modal
        document.getElementById('configuracionModal')?.addEventListener('hidden.bs.modal', () => {
            this.container.classList.add('d-none');
            this.header.classList.remove('d-none');
        });
    }
}

/* ── AnimationManager ─────────────────────────────── */
class AnimationManager {
    constructor() {
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    this.observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

        document.querySelectorAll('.animate-on-scroll, .stat-card').forEach(el => {
            this.observer.observe(el);
        });
    }
}

/* ── LoadingManager ───────────────────────────────── */
class LoadingManager {
    constructor() {
        this.overlay = document.getElementById('loadingOverlay');
    }

    show(message = 'Cargando...') {
        if (!this.overlay) return;
        const p = this.overlay.querySelector('p');
        if (p) p.textContent = message;
        this.overlay.style.display = 'flex';
    }

    hide() {
        if (this.overlay) this.overlay.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        const themeManager        = new ThemeManager();
        const sidebarManager      = new SidebarManager();
        const dropdownManager     = new DropdownManager();
        const searchManager       = new SearchManager();
        const notificationManager = new NotificationManager();
        const alertManager        = new AlertManager();
        const passwordManager     = new PasswordModalManager();
        const animationManager    = new AnimationManager();
        const loadingManager      = new LoadingManager();

        // Exponer globalmente
        window.notificationManager = notificationManager;
        window.app = {
            theme:         themeManager,
            sidebar:       sidebarManager,
            dropdown:      dropdownManager,
            search:        searchManager,
            notifications: notificationManager,
            alert:         AlertManager,
            loading:       loadingManager,
        };

        // Bootstrap: tooltips y popovers
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => new bootstrap.Popover(el));

        console.log('ITS CEP - Sistema de Gestión inicializado ✓');
    } catch (error) {
        console.error('Error al inicializar componentes:', error);
    }
});

window.utils = {
    formatCurrency(amount) {
        return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(amount);
    },

    formatDate(dateString) {
        return new Intl.DateTimeFormat('es-AR', {
            year: 'numeric', month: 'long', day: 'numeric'
        }).format(new Date(dateString));
    },

    debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    },

    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            AlertManager.showAlert('success', 'Texto copiado al portapapeles');
            return true;
        } catch {
            AlertManager.showAlert('danger', 'Error al copiar al portapapeles');
            return false;
        }
    },
};

/* Deshabilitar botón de submit al enviar formularios */
document.addEventListener('submit', (e) => {
    if (e.target.tagName !== 'FORM') return;
    const btn = e.target.querySelector('button[type="submit"]');
    if (btn) {
        btn.setAttribute('data-original-text', btn.innerHTML);
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';
    }
});