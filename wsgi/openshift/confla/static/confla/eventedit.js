function saveEvent() {
    console.log("foo");
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
    if ($(".modal-body form").length) modal.modal("show");

    $(".submit").click(saveEvent);

    // Show modal on click on an event
    $(".event").click(function () {
        showModal(this);
    });
})
