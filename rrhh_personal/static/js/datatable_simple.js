// DataTable simple para búsqueda de personal

$(document).ready(function() {
    const table = $('#personalLicenciaTable');
    if (table.length) {
        table.DataTable({
            paging: false,
            searching: false,
            info: false
        });
    }
});

