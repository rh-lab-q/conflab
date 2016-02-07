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
    });
}

$(document).ready(function() {
    setup_form($(".conf-form"));
});
