const TAB_KEY = 'da_tab_{{ alumno.uuid }}';
function cambiarTab(name) {
    document.querySelectorAll('.da-tab').forEach(t => t.classList.remove('act'));
    document.getElementById('tab-' + name).classList.add('act');
    document.querySelectorAll('.da-panels > div').forEach(p => p.classList.remove('act'));
    document.getElementById('panel-' + name).classList.add('act');
    try { sessionStorage.setItem(TAB_KEY, name); } catch(e) {}
}
(function() {
    try {
        const s = sessionStorage.getItem(TAB_KEY);
        if (s && document.getElementById('panel-' + s)) cambiarTab(s);
    } catch(e) {}
})();