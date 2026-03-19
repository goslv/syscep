document.addEventListener('DOMContentLoaded', function() {

    // Modal Docente
    document.getElementById('modalDocente').addEventListener('show.bs.modal', function(e) {
        const btn = e.relatedTarget;
        const materiaId   = btn.dataset.materiaId;
        const materiaNom  = btn.dataset.materiaNombre;
        const docenteId   = btn.dataset.docenteId;

        document.getElementById('materiaNombreDocente').textContent = materiaNom;
        document.getElementById('formAsignarDocente').action = `/materias/${materiaId}/asignar-docente/`;

        document.querySelectorAll('input[name="docente_id"]').forEach(r => r.checked = false);
        if (docenteId) {
            const r = document.querySelector(`input[name="docente_id"][value="${docenteId}"]`);
            if (r) r.checked = true;
        }
    });

    // Modal Fechas
    document.getElementById('modalFechas').addEventListener('show.bs.modal', function(e) {
        const btn = e.relatedTarget;
        document.getElementById('materiaNombreFechas').textContent = btn.dataset.materiaNombre;
        document.getElementById('formAsignarFechas').action = `/materias/${btn.dataset.materiaId}/asignar-fechas/`;
        document.getElementById('inputFechaParcial').value = btn.dataset.fechaParcial || '';
        document.getElementById('inputFechaFinal').value   = btn.dataset.fechaFinal   || '';
    });

});

function removerDocente() {
    document.querySelectorAll('input[name="docente_id"]').forEach(r => r.checked = false);
    document.getElementById('formAsignarDocente').submit();
}
