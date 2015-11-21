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
    $(".import-form").show();
}

function toggle_form () {
    var body = $(this).closest(".panel").find(".panel-body");
    var caret = $(this).find("i");
    if (caret.hasClass("fa-caret-down")) {
        caret.removeClass("fa-caret-down");
        caret.addClass("fa-caret-up");
        body.animate({height: body.get(0).scrollHeight}, 200);
    }
    else {
        caret.removeClass("fa-caret-up");
        caret.addClass("fa-caret-down");
        body.animate({height: 0}, 200);
    }
}

$(document).ready(function() {
    $(".panel-heading").click(toggle_form);
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
