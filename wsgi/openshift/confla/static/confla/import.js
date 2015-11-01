function showError(response) {
    $(".fa-spinner").remove();
    var resp = response.responseText;
    var div = '<div class="alert alert-danger"><i class="fa fa-exclamation-circle fa-lg"></i> Import error: ' + resp + '</div>';
    var alerts = '<div class="import-alerts">' + div + '</div>'
    $(".admin-page").prepend(alerts);
    $(".oa_form").show();
}

function showAlerts(response) {
    $(".fa-spinner").remove();
    $(".admin-page").prepend(response);
    $(".oa_form").show();
}

$(document).ready(function() {
    $(".oa_form").ajaxForm({
        success: showAlerts,
        error: showError,
        beforeSubmit: function () {
            $(".import-alerts").remove();
            spinner = '<div class="spinnerwrap"><i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i></div>';
            $(".oa_form").hide();
            $(".admin-page").prepend(spinner);
        }
    });
})
