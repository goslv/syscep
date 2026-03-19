
/* Modal imagen */
function abrirModalImagen(url) {
    const overlay  = document.getElementById('deModalImg');
    const img      = document.getElementById('deImgGrande');
    const download = document.getElementById('deDownloadBtn');
    img.src        = url;
    img.classList.remove('zoomed');
    download.href  = url;
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function cerrarModalImagen(e) {
    if (e && e.target !== document.getElementById('deModalImg') && e.type !== 'click') return;
    if (e && e.target.closest('.de-modal-actions')) return;
    document.getElementById('deModalImg').classList.remove('open');
    document.body.style.overflow = '';
}

function toggleZoom() {
    document.getElementById('deImgGrande').classList.toggle('zoomed');
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') cerrarModalImagen();
});

/* Modal eliminar */
function abrirModalEliminar() {
    new bootstrap.Modal(document.getElementById('modalEliminar')).show();
}