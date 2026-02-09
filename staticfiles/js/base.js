
class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('themeToggle');
        this.html = document.documentElement;
        this.init();
    }

    init() {
        // Cargar tema guardado o usar preferencia del sistema
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        let theme = savedTheme || (prefersDark ? 'dark' : 'light');
        this.setTheme(theme);

        // Inicializar botón toggle
        if (this.themeToggle) {
            this.updateToggleIcon(theme);
            this.themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Escuchar cambios en preferencias del sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    setTheme(theme) {
        this.html.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Actualizar icono si existe
        if (this.themeToggle) {
            this.updateToggleIcon(theme);
        }

        // Dispatch event para que otros componentes sepan del cambio
        document.dispatchEvent(new CustomEvent('themeChange', { detail: { theme } }));
    }

    toggleTheme() {
        const currentTheme = this.html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    updateToggleIcon(theme) {
        const icon = this.themeToggle.querySelector('i');
        if (icon) {
            icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
            // Añadir feedback visual extra
            this.themeToggle.classList.add('animate-spin-once');
            setTimeout(() => this.themeToggle.classList.remove('animate-spin-once'), 500);
        }
    }
}

// Sidebar Manager
class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.sidebarOverlay = document.getElementById('sidebarOverlay');
        this.menuToggle = document.getElementById('menuToggle');
        this.closeSidebar = document.getElementById('closeSidebar');
        this.body = document.body;
        this.isMobile = window.innerWidth <= 1024;

        this.init();
    }

    init() {
        this.bindEvents();
        this.detectMobile();
        this.setInitialState();
    }

    bindEvents() {
        this.menuToggle?.addEventListener('click', () => this.toggle());
        this.sidebarOverlay?.addEventListener('click', () => this.close());
        this.closeSidebar?.addEventListener('click', () => this.close());

        // Cerrar sidebar al hacer clic en enlace (móvil)
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (this.isMobile && this.sidebar.classList.contains('show')) {
                    this.close();
                }
            });
        });
    }

    toggle() {
        if (this.isMobile) {
            // En móvil, solo mostrar/ocultar
            this.sidebar.classList.toggle('show');
            this.sidebarOverlay.classList.toggle('show');
            this.body.style.overflow = this.sidebar.classList.contains('show') ? 'hidden' : '';
        } else {
            // En desktop, colapsar/expandir
            this.sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', this.sidebar.classList.contains('collapsed'));
        }
    }

    open() {
        this.sidebar.classList.add('show');
        this.sidebarOverlay.classList.add('show');
        this.body.style.overflow = 'hidden';
    }

    close() {
        this.sidebar.classList.remove('show');
        this.sidebarOverlay.classList.remove('show');
        this.body.style.overflow = '';
    }

    detectMobile() {
        const checkMobile = () => {
            this.isMobile = window.innerWidth <= 1024;
            if (!this.isMobile && this.sidebar.classList.contains('show')) {
                this.close();
            }
        };

        window.addEventListener('resize', checkMobile);
        checkMobile(); // Check inicial
    }

    setInitialState() {
        // Cargar estado del sidebar desde localStorage
        if (!this.isMobile && localStorage.getItem('sidebarCollapsed') === 'true') {
            this.sidebar.classList.add('collapsed');
        }
    }
}

// Dropdown Manager
class DropdownManager {
    constructor() {
        this.dropdowns = new Map();
        this.init();
    }

    init() {
        console.log('DropdownManager initializing');
        // Inicializar todos los dropdowns
        document.querySelectorAll('[data-dropdown]').forEach(dropdown => {
            const toggle = dropdown.querySelector('[data-dropdown-toggle]');
            const menu = dropdown.querySelector('[data-dropdown-menu]');

            if (toggle && menu) {
                this.dropdowns.set(dropdown, { toggle, menu, open: false });
                this.bindDropdownEvents(dropdown);
            }
        });

        // Dropdown del usuario (especial)
        const userDropdownToggle = document.getElementById('userDropdownToggle');
        const userDropdownMenu = document.getElementById('userDropdownMenu');

        if (userDropdownToggle && userDropdownMenu) {
            console.log('User dropdown elements found');
            userDropdownToggle.addEventListener('click', (e) => {
                console.log('User dropdown toggle clicked');
                e.preventDefault();
                e.stopPropagation();
                
                // Cerrar el de notificaciones si está abierto
                if (window.app && window.app.notifications) {
                    window.app.notifications.close();
                }
                
                const isShowing = userDropdownMenu.classList.contains('show');
                if (isShowing) {
                    userDropdownMenu.classList.remove('show');
                } else {
                    userDropdownMenu.classList.add('show');
                }
                userDropdownToggle.setAttribute('aria-expanded', !isShowing);
            });
        }

        // Cerrar dropdowns al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (userDropdownMenu && userDropdownToggle && !userDropdownToggle.contains(e.target) && !userDropdownMenu.contains(e.target)) {
                userDropdownMenu.classList.remove('show');
                userDropdownToggle.setAttribute('aria-expanded', 'false');
            }

            this.dropdowns.forEach((data, dropdown) => {
                if (!dropdown.contains(e.target) && data.open) {
                    this.closeDropdown(dropdown);
                }
            });
        });

        // Cerrar con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (userDropdownMenu && userDropdownToggle) {
                    userDropdownMenu.classList.remove('show');
                    userDropdownToggle.setAttribute('aria-expanded', 'false');
                }

                this.dropdowns.forEach((data, dropdown) => {
                    if (data.open) this.closeDropdown(dropdown);
                });
            }
        });
    }

    bindDropdownEvents(dropdown) {
        const { toggle, menu } = this.dropdowns.get(dropdown);

        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown(dropdown);
        });

        // Prevenir cierre al hacer clic dentro del menú
        menu.addEventListener('click', (e) => e.stopPropagation());
    }

    toggleDropdown(dropdown) {
        const data = this.dropdowns.get(dropdown);
        data.open ? this.closeDropdown(dropdown) : this.openDropdown(dropdown);
    }

    openDropdown(dropdown) {
        const data = this.dropdowns.get(dropdown);
        data.menu.classList.add('show');
        data.open = true;
        dropdown.setAttribute('data-state', 'open');
    }

    closeDropdown(dropdown) {
        const data = this.dropdowns.get(dropdown);
        data.menu.classList.remove('show');
        data.open = false;
        dropdown.setAttribute('data-state', 'closed');
    }
}

// Search Manager

class SearchManager {
    constructor() {
        this.searchInput = document.getElementById('globalSearch');
        this.searchContainer = document.getElementById('globalSearchContainer');
        this.searchToggleMobile = document.getElementById('searchToggleMobile');
        this.closeSearchMobile = document.getElementById('closeSearchMobile');
        this.init();
    }

    init() {
        if (!this.searchInput) return;

        // Toggle móvil
        this.searchToggleMobile?.addEventListener('click', () => {
            this.searchContainer?.classList.add('show-mobile');
            this.searchInput.focus();
        });

        this.closeSearchMobile?.addEventListener('click', () => {
            this.searchContainer?.classList.remove('show-mobile');
            this.searchInput.value = '';
        });

        // Manejar el envío de la búsqueda (Enter)
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = this.searchInput.value.trim();
                if (query) {
                    window.location.href = `/alumnos/?busqueda=${encodeURIComponent(query)}`;
                }
            }
        });

        // Atajo de teclado
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.searchInput.focus();
            }

            // Cerrar sidebar con Escape
            if (e.key === 'Escape') {
                const sidebar = document.getElementById('sidebar');
                const sidebarOverlay = document.getElementById('sidebarOverlay');

                if (sidebar && sidebar.classList.contains('show')) {
                    sidebar.classList.remove('show');
                    sidebarOverlay.classList.remove('show');
                    document.body.style.overflow = '';
                }

                // Quitar foco del search
                this.searchInput.blur();
            }
        });

        // Búsqueda en tiempo real
        this.searchInput.addEventListener('input', this.debounce(this.handleSearch, 300));

        // Placeholder dinámico
        this.searchInput.addEventListener('focus', () => {
            this.searchInput.setAttribute('placeholder', 'Presiona Ctrl+K para buscar rápidamente...');
        });

        this.searchInput.addEventListener('blur', () => {
            this.searchInput.setAttribute('placeholder', 'Buscar alumnos, pagos, carreras...');
        });
    }

    async handleSearch(e) {
        const query = e.target.value.trim();
        if (query.length < 2) return;

        try {
            // Aquí puedes implementar búsqueda AJAX
            console.log('Buscando:', query);
            // Ejemplo: const response = await fetch(`/api/search?q=${query}`);
        } catch (error) {
            console.error('Error en búsqueda:', error);
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Notification Manager
class NotificationManager {
    constructor() {
        this.toggleButton = document.getElementById('notificationsToggle');
        this.panel = document.getElementById('notificationPanel');
        this.list = document.getElementById('notificationList');
        this.count = document.getElementById('notificationCount');
        this.empty = document.getElementById('notificationEmpty');
        this.clearButton = document.getElementById('notificationsClear');
        this.dot = this.toggleButton?.querySelector('.notification-dot');
        this.isOpen = false;
        
        // Cargar notificaciones iniciales si el panel está vacío
        this.notifications = []; // Las notificaciones reales vienen del servidor
        this.init();
    }

    init() {
        if (!this.toggleButton || !this.panel || !this.list) {
            console.warn('Notification elements not found:', {
                toggle: !!this.toggleButton,
                panel: !!this.panel,
                list: !!this.list
            });
            return;
        }

        console.log('NotificationManager initialized');

        // Inicializar modales de Bootstrap
        this.modalDetalle = new bootstrap.Modal(document.getElementById('modalDetalleNotif'));
        this.modalHistorial = new bootstrap.Modal(document.getElementById('modalHistorialNotif'));
        this.historialList = document.getElementById('historialList');
        this.btnHistorial = document.getElementById('btnHistorialNotif');
        this.btnClearHistorial = document.getElementById('btnClearHistorial');

        // Verificar si hay notificaciones ya leídas persistidas
        this.checkPersistedNotifications();

        // Auto-close alerts after 5 seconds
        const alerts = document.querySelectorAll('.notifications-container .alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) bsAlert.close();
            }, 5000);
        });

        // NOTA: No llamamos a renderNotifications() para no sobreescribir el HTML del servidor
        // a menos que queramos manejar estados de "leído" localmente.
        // Pero checkPersistedNotifications ya lo llama si eliminó algo.
        
        // Si no se eliminó nada, igual sincronizamos el estado del dot/count inicial
        this.renderNotifications();

        this.toggleButton.addEventListener('click', (e) => {
            console.log('Notification toggle clicked');
            e.preventDefault();
            e.stopPropagation();
            this.toggle();
        });

        // Prevenir que clics dentro del panel lo cierren
        this.panel.addEventListener('click', (e) => {
            e.stopPropagation();
        });

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

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.close();
            }
        });
    }

    handleClick(element) {
        const isSolicitud = element.getAttribute('data-es-solicitud') === 'true';
        
        if (isSolicitud) {
            this.showDetail(element);
        } else {
            const url = element.getAttribute('data-url');
            this.markRead(element);
            if (url) {
                setTimeout(() => { window.location.href = url; }, 300);
            }
        }
    }

    showDetail(element, isFromHistory = false) {
        const title = element.getAttribute('data-type');
        const materia = element.getAttribute('data-materia');
        const carrera = element.getAttribute('data-carrera');
        const fecha = element.getAttribute('data-fecha');
        const isSolicitud = element.getAttribute('data-es-solicitud') === 'true';
        
        const titleEl = document.getElementById('notifTitle');
        const bodyEl = document.getElementById('notifBody');
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
            </div>
        `;
        
        if (isSolicitud) {
            const motivo = element.getAttribute('data-motivo');
            const urlProcesar = element.getAttribute('data-url-procesar');
            const solicitudId = element.getAttribute('data-solicitud-id');
            
            let datos = {};
            if (isFromHistory) {
                try { datos = JSON.parse(element.getAttribute('data-datos-objeto')); } catch(e) {}
            } else {
                const rawData = element.querySelector('script[id="temp"]')?.textContent;
                try { if(rawData) datos = JSON.parse(rawData); } catch(e) {}
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
                            ${Object.entries(datos).map(([k, v]) => `<li><strong>${k.charAt(0).toUpperCase() + k.slice(1)}:</strong> ${v}</li>`).join('')}
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
                </form>
            `;
            footerEl.style.display = 'none';
        } else {
            html += `<p>Notificación de sistema sobre el examen de ${materia}.</p>`;
            footerEl.style.display = 'flex';
        }
        
        bodyEl.innerHTML = html;
        this.modalDetalle.show();
        if (!isFromHistory) {
            this.markRead(element);
        }
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
                </div>
            `;
            this.btnClearHistorial.style.display = 'none';
            return;
        }
        
        this.btnClearHistorial.style.display = 'block';
        this.historialList.innerHTML = history.reverse().map(n => `
            <div class="list-group-item p-3 border-start-0 border-end-0 notification-history-item" 
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
                 onclick="window.notificationManager.handleHistoryClick(this)">
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
                        <div class="small text-muted mt-1">
                            ${n.materia} - ${n.carrera}
                        </div>
                        <div class="mt-2">
                            <span class="badge bg-light text-dark border small" style="font-size: 0.7rem;">Ver de nuevo</span>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    handleHistoryClick(element) {
        const isSolicitud = element.getAttribute('data-es-solicitud') === 'true';
        this.modalHistorial.hide();
        
        if (isSolicitud) {
            // Para solicitudes, mostramos el modal de detalle
            this.showDetail(element, true); // true indica que no debe marcarse como leído (ya lo está)
        } else {
            // Para exámenes, redirigir a la materia/carrera
            const url = element.getAttribute('data-url');
            if (url) {
                window.location.href = url;
            }
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    loadNotifications() {
        return []; // Desactivamos las notificaciones de ejemplo
    }

    saveNotifications() {
        // No guardamos nada por ahora
    }

    renderNotifications() {
        const items = this.list.querySelectorAll('.notification-item');
        const unreadCount = items.length;
        
        if (unreadCount === 0) {
            this.list.innerHTML = `
                <div class="notification-empty" id="notificationEmpty">
                    <i class="bi bi-bell-slash mb-2" style="font-size: 2rem; opacity: 0.3;"></i>
                    <p class="mb-0">No hay notificaciones nuevas</p>
                </div>
            `;
            if (this.dot && this.dot.style) {
                this.dot.style.display = 'none';
            }
            if (this.count) {
                this.count.textContent = '0';
                this.count.classList.add('d-none');
            }
            return;
        }

        if (this.count) {
            this.count.textContent = unreadCount;
            this.count.classList.remove('d-none');
        }
        if (this.dot && this.dot.style) {
            this.dot.style.display = 'block';
        }
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        console.log('Opening notification panel');
        // Cerrar el dropdown de usuario si está abierto
        const userDropdownMenu = document.getElementById('userDropdownMenu');
        const userDropdownToggle = document.getElementById('userDropdownToggle');
        if (userDropdownMenu) {
            userDropdownMenu.classList.remove('show');
            if (userDropdownToggle) userDropdownToggle.setAttribute('aria-expanded', 'false');
        }

        this.panel.classList.add('show');
        this.toggleButton.setAttribute('aria-expanded', 'true');
        this.toggleButton.classList.add('active');
        this.isOpen = true;
        console.log('Panel status: show class added');

        // Ocultar el punto rojo al abrir el panel
        if (this.dot) {
            this.dot.style.display = 'none';
        }
    }

    close() {
        if (!this.isOpen) return;
        console.log('Closing notification panel');
        this.panel.classList.remove('show');
        this.toggleButton.setAttribute('aria-expanded', 'false');
        this.toggleButton.classList.remove('active');
        this.isOpen = false;
    }

    markRead(element) {
        if (element && element.classList.contains('notification-item')) {
            element.classList.remove('unread');
            element.classList.add('is-read');
            
            // Guardar en localStorage que esta notificación fue leída
            this.persistReadState(element);
            
            setTimeout(() => {
                element.style.opacity = '0';
                element.style.transform = 'translateX(20px)';
                element.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    element.remove();
                    this.renderNotifications();
                }, 300);
            }, 300);
        }
    }

    markAllRead() {
        const items = this.list.querySelectorAll('.notification-item');
        items.forEach(item => {
            item.classList.add('fade-out');
            this.persistReadState(item);
        });
        
        setTimeout(() => {
            this.list.innerHTML = '';
            this.renderNotifications();
        }, 300);
    }

    // Persistencia simple usando localStorage
    persistReadState(element) {
        const type = element.getAttribute('data-type');
        const materia = element.getAttribute('data-materia');
        const carrera = element.getAttribute('data-carrera');
        const date = element.getAttribute('data-fecha');
        const icon = element.getAttribute('data-icon');
        const color = element.getAttribute('data-color');
        const url = element.getAttribute('data-url');
        const esSolicitud = element.getAttribute('data-es-solicitud') === 'true';
        const motivo = element.getAttribute('data-motivo');
        const urlProcesar = element.getAttribute('data-url-procesar');
        const solicitudId = element.getAttribute('data-solicitud-id');
        
        let datosObjeto = {};
        if (esSolicitud) {
            const rawData = element.querySelector('script[id="temp"]')?.textContent;
            try { if(rawData) datosObjeto = JSON.parse(rawData); } catch(e) {}
        }
        
        if (type && materia && date) {
            const id = btoa(`${type}-${materia}-${date}`); // Crear un ID simple
            
            // 1. Guardar IDs leídos
            let readNotifications = JSON.parse(localStorage.getItem('readNotifications') || '[]');
            if (!readNotifications.includes(id)) {
                readNotifications.push(id);
                if (readNotifications.length > 100) readNotifications.shift();
                localStorage.setItem('readNotifications', JSON.stringify(readNotifications));
            }
            
            // 2. Guardar en historial
            let history = JSON.parse(localStorage.getItem('notifHistory') || '[]');
            // Evitar duplicados en historial
            if (!history.find(n => n.id === id)) {
                history.push({ 
                    id, type, materia, carrera, date, icon, color, url,
                    es_solicitud: esSolicitud,
                    motivo, url_procesar: urlProcesar, solicitud_id: solicitudId,
                    datos_objeto: datosObjeto
                });
                if (history.length > 50) history.shift();
                localStorage.setItem('notifHistory', JSON.stringify(history));
            }
        }
    }

    checkPersistedNotifications() {
        const readNotifications = JSON.parse(localStorage.getItem('readNotifications') || '[]');
        const items = this.list.querySelectorAll('.notification-item');
        let countRemoved = 0;

        items.forEach(item => {
            const type = item.getAttribute('data-type');
            const materia = item.getAttribute('data-materia');
            const date = item.getAttribute('data-fecha');
            
            if (type && materia && date) {
                const id = btoa(`${type}-${materia}-${date}`);
                if (readNotifications.includes(id)) {
                    item.remove();
                    countRemoved++;
                }
            }
        });

        if (countRemoved > 0) {
            this.renderNotifications();
        }
    }
}

// Alert Manager
class AlertManager {
    constructor() {
        this.init();
    }

    init() {
        // Auto-cerrar alertas
        document.querySelectorAll('.alert-auto-close').forEach(alert => {
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }, 5000);
        });

        // Cerrar todas las alertas
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('alert-close-all')) {
                document.querySelectorAll('.alert-custom').forEach(alert => {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                    bsAlert.close();
                });
            }
        });
    }

    static showAlert(type, message, title = null) {
        const alertTypes = {
            'success': { icon: 'bi-check-lg', defaultTitle: '¡Éxito!' },
            'warning': { icon: 'bi-exclamation-lg', defaultTitle: 'Advertencia' },
            'danger': { icon: 'bi-x-lg', defaultTitle: 'Error' },
            'info': { icon: 'bi-info-lg', defaultTitle: 'Información' }
        };

        const alertType = alertTypes[type] || alertTypes.info;
        const alertTitle = title || alertType.defaultTitle;

        const alertHtml = `
            <div class="alert-custom alert-${type} alert-dismissible fade show alert-auto-close" role="alert">
                <div class="alert-icon">
                    <i class="bi ${alertType.icon}"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-title">${alertTitle}</div>
                    ${message}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
            </div>
        `;

        const container = document.querySelector('.content-wrapper');
        if (container) {
            const firstChild = container.firstChild;
            if (firstChild && firstChild.classList && firstChild.classList.contains('alert-custom')) {
                firstChild.insertAdjacentHTML('afterend', alertHtml);
            } else {
                container.insertAdjacentHTML('afterbegin', alertHtml);
            }
        }

        // Auto-cerrar
        setTimeout(() => {
            const alert = document.querySelector('.alert-custom:last-child');
            if (alert) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Animation Manager
class AnimationManager {
    constructor() {
        this.observer = null;
        this.init();
    }

    init() {
        // Configurar Intersection Observer
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    this.observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        // Observar elementos con animación
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            this.observer.observe(el);
        });

        // Animación de entrada para stat cards
        document.querySelectorAll('.stat-card').forEach(card => {
            card.classList.add('animate-on-scroll');
            this.observer.observe(card);
        });
    }
}

// Loading Manager
class LoadingManager {
    constructor() {
        this.loadingOverlay = document.getElementById('loadingOverlay');
    }

    show(message = 'Cargando...') {
        if (this.loadingOverlay) {
            const textElement = this.loadingOverlay.querySelector('p');
            if (textElement) {
                textElement.textContent = message;
            }
            this.loadingOverlay.style.display = 'flex';
        }
    }

    hide() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }
}

// Inicialización Principal
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded: Initializing components...');
    // Inicializar componentes
    try {
        const themeManager = new ThemeManager();
        console.log('ThemeManager initialized');
        const sidebarManager = new SidebarManager();
        console.log('SidebarManager initialized');
        const dropdownManager = new DropdownManager();
        console.log('DropdownManager initialized');
        const searchManager = new SearchManager();
        console.log('SearchManager initialized');
        const notificationManager = new NotificationManager();
        console.log('NotificationManager initialized');
        window.notificationManager = notificationManager; // Acceso directo para onclick
        const alertManager = new AlertManager();
        console.log('AlertManager initialized');
        const animationManager = new AnimationManager();
        console.log('AnimationManager initialized');
        const loadingManager = new LoadingManager();
        console.log('LoadingManager initialized');

        // Exponer componentes globalmente para acceso desde otros scripts
        window.app = {
            theme: themeManager,
            sidebar: sidebarManager,
            dropdown: dropdownManager,
            search: searchManager,
            notifications: notificationManager,
            alert: AlertManager,
            loading: loadingManager
        };
    } catch (error) {
        console.error('Error initializing components:', error);
    }

    // Inicializar tooltips de Bootstrap
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltips.length > 0 && bootstrap.Tooltip) {
        [...tooltips].map(tooltip => new bootstrap.Tooltip(tooltip));
    }

    // Inicializar popovers de Bootstrap
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    if (popovers.length > 0 && bootstrap.Popover) {
        [...popovers].map(popover => new bootstrap.Popover(popover));
    }

    // Mostrar mensaje de bienvenida en consola
    console.log('ITS CEP - Sistema de Gestión inicializado');
});

// Funciones de utilidad globales

window.utils = {
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('es-AR', {
            style: 'currency',
            currency: 'ARS'
        }).format(amount);
    },

    formatDate: function(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('es-AR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(date);
    },

    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    copyToClipboard: async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            AlertManager.showAlert('success', 'Texto copiado al portapapeles');
            return true;
        } catch (err) {
            console.error('Error al copiar: ', err);
            AlertManager.showAlert('danger', 'Error al copiar al portapapeles');
            return false;
        }
    }
};

// Handlers para AJAX y formularios

document.addEventListener('submit', function(e) {
    // Mostrar loading en formularios
    if (e.target.tagName === 'FORM') {
        const submitBtn = e.target.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';
        }
    }
});

// Restaurar botones de formulario después de submit
document.addEventListener('ajax:complete', function(e) {
    const form = e.target.closest('form');
    if (form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Enviar';
        }
    }
});
