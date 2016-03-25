function setup_url_field() {
    $("#id_name").change(function() {
        $("#id_url_id").val($(this).val().replace(/ /g,'').toLowerCase());
        return false;
    }).keyup(function() {
        $(this).change();
    });
}

function setup_form(form){
    $(form).find(".selectized-input").selectize({
        create: function(input, callback) {
            var def = $.post(room_link, {
                csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
                data: input
            });
            $.when(def).then(function (response){
                // Success
                callback({ value: response, text: input });
            });
        },
        persist: true,
        plugins: ['drag_drop'],
        maxItems: null,
        options: rooms,
        valueField: 'id',
        labelField: 'name',
        searchField: ['name'],
    });

    $('.input-daterange').each(function() {
        $(this).datepicker({ format : "yyyy-mm-dd"});
    });

    setup_url_field();
}

$(document).ready(function() {
    setup_form($(".conf-form"));
});
