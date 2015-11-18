function changeView() {
    var sel = $(".sel-view option:selected").text();
    switch (sel) {
        case "List": {
            $.when($.get(list_link)).then(function(response) {
                // Success
                $(".sched-wrap:visible").html($(response).find(".schedlist-wrap").html());
                $(".sched-wrap:visible").removeClass().addClass("schedlist-wrap");
                userPopoverInit();
            }, function (response){
                // Failure
                show_error("schedule list", response);
            })
            break;
        };
        case "Grid": {
            $.when($.get(user_link)).then(function(response) {
                // Success
                $(".schedlist-wrap").html($(response).find(".sched-wrap").html());
                $(".schedlist-wrap").removeClass().addClass("sched-wrap");
                user_setup();
            }, function (response){
                // Failure
                show_error("schedule grid", response);
            });
            break;
        }
    }
}

function changeDay() {
    var active = $("#sched-tabs .active");
    $(".day-wrap[day-id=" + $(this).attr("day-id") + "]").show();
    $(".day-wrap[day-id=" + active.attr("day-id") + "]").hide();
    active.removeClass("active");
    $(this).addClass("active");
    $(this).off("click");
    active.click(changeDay);
}

function userPopoverInit() {
    $(".user-wrap .item").each (function () {
        var itemp = this;
        var mousepos = {top: 0, left: 0, height: 0, width: 0};
        var arrowsize = 11; // arrow size in pixels
        $(itemp).click(function(e){
            mousepos.top = e.pageY;
            mousepos.left = e.pageX;
        }).popover({
            placement: "bottom",
            html: "true",
            title: " ",
            container: "body",
            template: '<div class="popover pop-user" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>',
            content: function () {
                var content = $(itemp).find(".pop-content");
                // If the content has not been fetched yet
                if (!content.length) {
                    spinner = '<i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i>';
                    // Send a post and monitor the promise object
                    def = $.post("/events/popover/", {
                        csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
                        data: $(".event", this).attr("event-id"),
                    });
                    $.when(def).then(function (response){
                        // Success
                        var popid = "#" + $(itemp).attr("aria-describedby");
                        var pop = $(popid)[0];
                        $(popid).find(".fa-spinner").remove();
                        $(popid).find(".popover-content").append(response);
                        // Compute the popover position using bootstrap's popover prototype
                        var position = $.fn.popover.Constructor.prototype.getCalculatedOffset(
                                'bottom', mousepos, pop.offsetWidth, pop.offsetHeight);
                        // Adjust to arrow size
                        position.top = position.top + arrowsize + 1;
                        // Save new position
                        $(popid).offset(position);
                        div = document.createElement("div");
                        div.className = "pop-content";
                        $(div).append($(response).clone()).hide();
                        $(itemp).find(".event").append(div);
                    }, function(response) {
                        // Failure
                        $("[aria-describedby]").popover("hide");
                        alert("Something went wrong!");
                    });
                    return spinner;
                } else
                    // Content has already been fetched from the server
                    return content.clone().show();
            }
        }).on("show.bs.popover", function() {
            // Hide all other popovers when showing a new one
            $("[aria-describedby]").not(this).popover("hide");
        }).on("shown.bs.popover", function() {
            // Adjust the popover position
            var popid = "#" + $(itemp).attr("aria-describedby");
            var pop = $(popid)[0];
            // Compute the popover position using bootstrap's popover prototype
            var position = $.fn.popover.Constructor.prototype.getCalculatedOffset(
                    'bottom', mousepos, pop.offsetWidth, pop.offsetHeight);
            // Adjust to arrow size
            position.top = position.top + arrowsize + 1;
            // Save new position
            $(popid).offset(position);
            $(popid).css('visibility', 'visible');
        }).on("hide.bs.popover", function() {
            var popid = "#" + $(itemp).attr("aria-describedby");
            $(popid).css('visibility', 'hidden');
        });
    });
}

function user_setup() {
    userPopoverInit();

    // Setup tabs for days
    $("#sched-tabs li:not(.active)").click(changeDay);

    // Close all popovers if clicked outside of a popover or an event
    sel = ".user-wrap .item";
    $('html').on('click', function(e) {
        // If the target is not an event or topic
        if (!$(e.target).hasClass("event-visible") && !$(e.target).hasClass("topic") && !$(e.target).hasClass("speaker")
            && !$(e.target).hasClass("speakers")
                // If the target is not a popover
            && $(e.target).parents('.popover.in').length === 0) {
                $(sel).each( function () {
                // If there is an open popover, hide it
                if ($(this).attr("aria-describedby")) {
                   $(this).popover('hide');
                }
            });
        }
    });

    // Delete empty rooms
    $(".user-wrap .table").each(function() {
        var that = this;
        // For each room name table header except the first one (time)
        $("th:not(:first-child)", this).each(function() {
            var index = $(this).index() + 1;
            // If there are cells in a column given by "index" that dont have any events
            if (!$("td:nth-child("+ index +") .event", that).length) {
                $("td:nth-child("+ index +")", that).remove();
                $(this).remove();
            }
        });
    });
}

$(document).ready(function() {
    user_setup();
})
