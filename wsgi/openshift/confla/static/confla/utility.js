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

$(document).ready(function() {
    $(".confla-toggle").click(confla_toggle);
})
