function showError(response) {
    $(".fa-spinner").remove();
    var resp = response.responseText;
    var div = '<div class="alert alert-danger"><i class="fa fa-exclamation-circle fa-lg"></i> Import error: <pre>' + resp + '</pre> </div>';
    var alerts = '<div class="import-alerts">' + div + '</div>'
    $(".admin-page").prepend(alerts);
    $(".oa_form").show();
}

function showAlerts(response) {
    $(".fa-spinner").remove();
    $(".admin-page").prepend(response);
    $(".import-form").show();
    $(".confla-toggle.alert-header").click(confla_toggle);
}

function import_event(selector) {
    var json = $(selector).closest("li").find(".event-json").text();
    def = $.post("import_event/", {
        csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
        data: json});
    $.when(def).then(function (){
    }, function (response){
    });
}

$(document).ready(function() {
    $(".admin-page form").ajaxForm({
        success: showAlerts,
        error: showError,
        beforeSubmit: function () {
            $(".import-alerts").remove();
            spinner = '<div class="spinnerwrap"><i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i></div>';
            $(".import-form").hide();
            $(".admin-page").prepend(spinner);
        }
    });
})
