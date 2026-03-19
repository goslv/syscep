
document.addEventListener('DOMContentLoaded', function() {
    const btnToggle = document.getElementById('btnTogglePassword');
    const btnCancel = document.getElementById('btnCancelPassword');
    const formContainer = document.getElementById('passwordFormContainer');
    let isFormVisible = false;

    // Función para mostrar el formulario
    function showForm() {
        formContainer.style.display = 'block';
        isFormVisible = true;

        // Smooth scroll al formulario
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Función para ocultar el formulario
    function hideForm() {
        formContainer.style.display = 'none';
        isFormVisible = false;
    }

    btnToggle.addEventListener('click', showForm);
    btnCancel.addEventListener('click', hideForm);

    // Detectar tema actual
    function updateThemeDisplay() {
        const themeBadge = document.getElementById('currentTheme');
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        themeBadge.textContent = isDark ? 'Oscuro' : 'Claro';
    }

    // Escuchar cambios de tema
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                updateThemeDisplay();
            }
        });
    });

    observer.observe(document.documentElement, { attributes: true });
    updateThemeDisplay();

    // Validación de contraseña en tiempo real (opcional)
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        field.addEventListener('input', function() {
            // Validación simple de longitud
            if (this.name === 'new_password1' && this.value.length > 0 && this.value.length < 8) {
                this.style.borderColor = 'var(--cf-danger)';
            } else {
                this.style.borderColor = '';
            }
        });
    });
});
