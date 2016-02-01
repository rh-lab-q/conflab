function confla_toggle () {
    console.log($(this));
    var body = $(this).parent().find(".confla-togglable");
    var caret = $(this).find(".confla-caret");
    if (body.hasClass("toggled")) {
        caret.removeClass("fa-caret-up");
        caret.addClass("fa-caret-down");
        body.animate({height: 0}, 200, function() {
            $(this).removeClass("toggled");
        });
    }
    else {
        caret.removeClass("fa-caret-down");
        caret.addClass("fa-caret-up");
        body.addClass("toggled");
        body.animate({height: body.get(0).scrollHeight}, 200);
    }
}

function toggle_events(tag) {
    // Get the tag's class
    $(this).toggleClass("tag-color");
    var tag_name = $(this)[0].classList[0];
    $(this).toggleClass("tag-color");
    // Toggle event visibility for given tag
    var items = $(".sched-wrap ." + tag_name).closest(".item");
    if ($(this).hasClass("tag-disabled"))
        items.show();
    else
        items.hide();
    items.toggleClass("item-disabled");
    // Hide empty rooms
    $(".sched-wrap .table").each(function() {
        var that = this;
        // For each room name table header except the first one (time)
        $("th:not(:first-child)", this).each(function() {
            var index = $(this).index() + 1;
            // If there are cells in a column given by "index" that dont have any events
            if (!$("td:nth-child("+ index +") .item:not(.item-disabled)", that).length) {
                $("td:nth-child("+ index +")", that).hide();
                $(this).hide();
            }
            else {
                $("td:nth-child("+ index +")", that).show();
                $(this).show();
            }
        });
    });
    $(this).toggleClass("tag-disabled");
}

function legendInit() {
    $("#legend-wrap .tag-color").each(function () {
        $(this).click(toggle_events);
    });
}

$(document).ready(function() {
    $(".confla-toggle").click(confla_toggle);
})
