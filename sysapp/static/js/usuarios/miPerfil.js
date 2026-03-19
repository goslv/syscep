// Validación simple de email (opcional)
document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.querySelector('input[name="email"]');

    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const email = this.value;
            if (email && !email.includes('@')) {
                this.style.borderColor = 'var(--mp-danger)';

                // Mostrar mensaje de error si no existe
                if (!this.nextElementSibling?.classList.contains('mp-error')) {
                    const error = document.createElement('div');
                    error.className = 'mp-error';
                    error.innerHTML = '<i class="bi bi-exclamation-circle"></i> Ingresa un email válido';
                    this.parentNode.appendChild(error);
                }
            } else {
                this.style.borderColor = '';
                const error = this.parentNode.querySelector('.mp-error');
                if (error) error.remove();
            }
        });
    }

    // Animación del avatar (pausar al hacer hover)
    const avatar = document.querySelector('.mp-avatar');
    if (avatar) {
        avatar.addEventListener('mouseenter', () => {
            avatar.style.animation = 'none';
        });
        avatar.addEventListener('mouseleave', () => {
            avatar.style.animation = 'pulse 2s ease infinite';
        });
    }
});
