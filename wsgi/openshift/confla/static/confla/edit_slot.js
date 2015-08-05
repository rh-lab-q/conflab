$(document).ready(function() {
    $(".fieldset-content:visible .room-select").each(function() {
        var that = this;
        $(this).selectize({
            persist: false,
            plugins: ['remove_button'],
            maxItems: null,
            valueField: 'room_value',
            labelField: 'room_name',
            searchField: ['room_name'],
            render: {
                item: function(item, escape) {
                    return '<div>' +
                        (item.room_name ? '<span class="name">' + escape(item.room_name) + ' </span>' : '') +
                    '</div>';
                },
                option: function(item, escape) {
                    var label = item.room_name;
                    return '<div>' +
                        '<span>' + escape(label) + '</span>' +
                    '</div>';
                }
            },
            onItemRemove: function(value) {
                // Add removed item to other selects
                $(".fieldset-content:visible select.room-select").each(function () {
                    var sel = $(this)[0].selectize;
                    sel.addOption({room_value: value, room_name: value});
                    sel.refreshOptions(false);
                });
            },
            onItemAdd: function(value, $item) {
                // Remove added item from other selects
                $(".fieldset-content:visible select.room-select").each(function () {
                    // If this is a different select
                    if (!$(this).is(that)) {
                        var sel = $(this)[0].selectize;
                        sel.removeOption(value);
                        sel.refreshOptions(false);
                    }
                });
            },
        });
    });
});
