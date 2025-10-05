$(document).ready(function () {
    $('#personalTable').DataTable({
        dom: 'Bfrtip', // Activa botones junto con búsqueda, filtros, etc.
        buttons: [
            'copy', 'csv', 'excel', 'pdf', 'print' // Botones que deseas incluir
        ],
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' // Traducción al español
        }
    });
});
