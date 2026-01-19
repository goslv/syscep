// ========================================
// Theme Manager - Modo Oscuro/Claro
// ========================================
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
        }
    }
}

// ========================================
// Sidebar Manager
// ========================================
class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.sidebarOverlay = document.getElementById('sidebarOverlay');
        this.menuToggle = document.getElementById('menuToggle');
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

// ========================================
// Dropdown Manager
// ========================================
class DropdownManager {
    constructor() {
        this.dropdowns = new Map();
        this.init();
    }

    init() {
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
            userDropdownToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                userDropdownMenu.classList.toggle('show');
            });
        }

        // Cerrar dropdowns al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (userDropdownMenu && !userDropdownToggle.contains(e.target) && !userDropdownMenu.contains(e.target)) {
                userDropdownMenu.classList.remove('show');
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
                if (userDropdownMenu) {
                    userDropdownMenu.classList.remove('show');
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
        this.init();
    }

    init() {
        if (!this.searchInput) return;

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

// ========================================
// Alert Manager
// ========================================
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

    // Método para mostrar alertas dinámicas
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

// ========================================
// Animation Manager
// ========================================
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

// ========================================
// Loading Manager
// ========================================
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

// ========================================
// Inicialización Principal
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar componentes
    const themeManager = new ThemeManager();
    const sidebarManager = new SidebarManager();
    const dropdownManager = new DropdownManager();
    const searchManager = new SearchManager();
    const alertManager = new AlertManager();
    const animationManager = new AnimationManager();
    const loadingManager = new LoadingManager();

    // Exponer componentes globalmente para acceso desde otros scripts
    window.app = {
        theme: themeManager,
        sidebar: sidebarManager,
        dropdown: dropdownManager,
        search: searchManager,
        alert: AlertManager, // Métodos estáticos
        loading: loadingManager
    };

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

// ========================================
// Funciones de utilidad globales
// ========================================
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