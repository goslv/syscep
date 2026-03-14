document.getElementById('btnAddAnother')?.addEventListener('click', function () {
    document.getElementById('addAnotherFlag').value = '1';
    document.getElementById('faForm').submit();
});

/* Asegurarse de que el botón principal NO lleve el flag */
document.getElementById('btnSubmit')?.addEventListener('click', function () {
    document.getElementById('addAnotherFlag').value = '0';
});