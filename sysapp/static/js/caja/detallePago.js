/* ── Modal imagen ───────────────────────────────────────────── */
function abrirModalImagen(url) {
    const overlay  = document.getElementById('dpModalImg');
    const img      = document.getElementById('dpImgGrande');
    const download = document.getElementById('dpDownloadBtn');
    img.src        = url;
    img.classList.remove('zoomed');
    download.href  = url;
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function cerrarModalImagen(e) {
    if (e && e.target !== document.getElementById('dpModalImg') && e.type !== 'click') return;
    if (e && e.target.closest('.dp-modal-actions')) return;
    document.getElementById('dpModalImg').classList.remove('open');
    document.body.style.overflow = '';
}

function toggleZoom() {
    document.getElementById('dpImgGrande').classList.toggle('zoomed');
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') cerrarModalImagen();
});

/* ── Modal eliminar ─────────────────────────────────────────── */
function abrirModalEliminar() {
    new bootstrap.Modal(document.getElementById('modalEliminar')).show();
}