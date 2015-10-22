function showAlerts(response) {
    $(".import-alerts").remove();
    $(".admin-page").prepend(response);
}

$(document).ready(function() {
    $(".oa_form").ajaxForm({
        success: showAlerts 
    });
})
