function saveEvent() {
    $(".modal-body form").ajaxSubmit({
        success: function(response) {
            console.log("ok");
        }
    });
    $(".modal").modal("hide");
}

function showModal(event) {
    var modal = $(".modal");
    def = $.post("/events/modal/", {
                    csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
                    data: $(event).attr("event-id"),
        });
    modal.modal("show");
    $.when(def).then(function (response){
        // Success
        $(".modal-body").html($(".mod-content", response).html());
        $(".modal-body form").ajaxForm();
    }, function (response){
        $(".modal").modal("hide");
        alert("Something went wrong!");
    });
}

$(document).ready(function() {
    // Setup modal
    var modal = $(".modal").modal({
        show: false
    })
    var form = $(".modal-body form");
    if (form.length) {
        $(form).ajaxForm();
        modal.modal("show");
    }

    $(".submit").click(saveEvent);

    // Show modal on click on an event
    $(".event").click(function () {
        showModal(this);
    });
})
