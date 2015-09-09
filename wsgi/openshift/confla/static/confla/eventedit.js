function saveEvent() {
    $(".modal-body form").ajaxSubmit({
        success: function(response) {
            console.log("ok");
        }
    });
    $(".modal").modal("hide");
}

function selectizeModal(selector) {
    // Selectize speaker select
    var speaker = $(selector).find("#id_speaker");
    var speakerlist = [];
    // Setup list of selected users
    $(speaker).find("[selected='selected']").each(function () {
        speakerlist.push($(this).text());
    });
    $(speaker).selectize({
        persist: false,
        maxItems: null,
        valueField: 'username',
        labelField: 'name',
        searchField: ['name', 'username'],
        options: users,
        items: speakerlist,
        render: {
            item: function(item, escape) {
                return '<div>' +
                    (item.name ? '<span class="name">' + escape(item.name) + ' </span>' : '') +
                    (item.username ? '<span class="username">(' + escape(item.username) + ')</span>' : '') +
                '</div>';
            },
            option: function(item, escape) {
                var username = item.username;
                var name = item.name;
                return '<div>' +
                    '<span class="name">' + escape(name) + '</span>' +
                    '<span class="username">(' + escape(username) + ')</span>' +
                '</div>';
            }
        }
    });
    // Selectize tags select
    var tag = $(selector).find("#id_tags");
    var taglist = [];
    // Setup list of selected tags
    $(tag).find("[selected='selected']").each(function () {
        taglist.push($(this).val());
    });
    $(tag).selectize({
        plugins: ['drag_drop'],
        persist: false,
        maxItems: null,
        valueField: 'id',
        labelField: 'name',
        searchField: ['name'],
        items: taglist,
        render: {
            item: function(item, escape) {
                return '<div>' +
                    '<span class="name">' + escape(item.name) + ' </span>' +
                '</div>';
            },
            option: function(item, escape) {
                var caption = item.name;
                return '<div>' +
                    '<span class="caption">' + escape(caption) + '</span>' +
                        '</div>';
            }
        }
    });
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
        $(".modal-body").html($(".modal-body", response).html());
        selectizeModal(".modal-body");
        $(".modal-body form").ajaxForm();
    }, function (response){
        $(".modal").modal("hide");
        alert("Something went wrong!");
    });
}

function setupModal(selector) {
    var modal = $(selector).modal({
        show: false
    })
    var form = $("form", modal);
    if (form.length) {
        $(form).ajaxForm();
        selectizeModal(form);
        modal.modal("show");
    }

    $(".submit").click(saveEvent);

}

$(document).ready(function() {
    // Setup modal
    if ($(".event-edit .modal").length) {
        setupModal(".modal");
        // Show modal on click on an event
        $(".event").click(function () {
            showModal(this);
        });
    }
})
