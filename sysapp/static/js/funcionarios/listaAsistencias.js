// Toggle filtros
function toggleFilters() {
    const card = document.getElementById('filtersCard');
    card.classList.toggle('collapsed');
}

// Inicializar estado de filtros
(function() {
    const params = new URLSearchParams(window.location.search);
    const hasFilters = params.get('funcionario') || params.get('fecha');
    const filtersCard = document.getElementById('filtersCard');

    if (!hasFilters && filtersCard) {
        filtersCard.classList.add('collapsed');
    }
})();

// Animaciones
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.la-stat').forEach((stat, index) => {
        stat.style.animationDelay = `${index * 0.05}s`;
    });
});
