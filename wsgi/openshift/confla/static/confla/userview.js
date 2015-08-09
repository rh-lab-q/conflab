function confirm() {
    var defer = $.Deferred();
    $('<div></div>').html("Save changes?")
        .dialog({
            autoOpen: true,
            modal: true,
            title: 'Save',
            buttons: {
                "Yes": function () {
                    defer.resolve("yes");
                    $(this).dialog("close");
                },
                "No": function () {
                    defer.resolve("no");
                    $(this).dialog("close");
                },
                "Cancel": function () {
                    defer.resolve("cancel");
                    $(this).dialog("close");
                }
            },
            close: function () {
                $(this).remove();
            }
        }).css("z-index", 10000);
    return defer.promise();
}

function changeView() {
    var sel = $(".sel-view option:selected").text();
    switch (sel) {
        case "List": {
            $.get( "/sched/list/", function( data ) {
                $(".sched-wrap:visible").html($(data).find(".schedlist-wrap").html());
                $(".sched-wrap:visible").removeClass().addClass("schedlist-wrap");
                userPopoverInit();
            })
            break;
        };
        case "Grid": {
            $.get( "/sched/", function( data ) {
                $(".schedlist-wrap").html($(data).find(".sched-wrap").html());
                $(".schedlist-wrap").removeClass().addClass("sched-wrap");
                user_setup();
            });
            break;
        }
    }
}

function userPopoverInit() {
    $(".user-wrap .item").each (function () {
        var itemp = this;
        $(itemp).popover({
            placement: "bottom",
            html: "true",
            title: " ",
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
                        $(popid).find(".fa-spinner").remove();
                        $(popid).find(".popover-content").append(response);
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
        });
    });
}

function loadUserview() {
    $.get( "/sched/", function( data ) {
        var wrap = document.createElement('div');
        wrap.className = "user-wrap";
        $(wrap).append($(data).find(".display-style"));
        $(wrap).append($(data).find(".sched-wrap"));
        $(wrap).hide();
        user_setup();
        $("body > .container:not(#event-bar)").append(wrap);
        $(".fa-spinner").remove();
        $(wrap).show();
    });
}

function showUsersched() {
    if ($(".active > a", "#sched-tabs").is("#tab-adminsched")) {
        // Went from adminsched to usersched
        getUserSched();
        $("#tab-adminsched").off("click").click(showAdminsched);
    } else if ($(".active > a", "#sched-tabs").is("#tab-fillsched")) {
        // Went from fillsched to usersched
        $("#tab-usersched").off("click");
        $("#tab-fillsched").off("click").click(showFillsched);
        $("#sched-tabs").find("li.active").removeClass("active");
        $(this).parent().addClass("active");
    }
}

function showRoomConfig() {
    console.log("show room config");
}

function showAdminsched() {
    $("#tab-adminsched").off("click");
    if ($(".active > a", "#sched-tabs").is("#tab-usersched")) {
        // Went from usersched to adminsched
        getAdminSched();
        $("#tab-usersched").off("click").click(showUsersched);
    } else if ($(".active > a", "#sched-tabs").is("#tab-fillsched")) {
        // Went from confsched to adminsched
        $("#tab-fillsched").off("click").click(showFillsched);
    }
    $("#sched-tabs").find("li.active").removeClass("active");
    $(this).parent().addClass("active");
}

function getAdminSched() {
    if ($(".admin-wrap").length) {
        // Admin view is already present
        $(".edit-btns").show();
        $(".user-wrap").remove();
        timetableEdit();
        $(".admin-wrap").show();
        $("#event-bar").show();
    }
    else {
        // Need to load the admin view from the server
        content = $("body > .container:not(.event-bar)");
        spinner = '<i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i>';
        $(".user-wrap").remove();
        $(content).append(spinner);
        $.get( "/admin/sched/", function( data ) {
            var wrap = document.createElement('div');
            wrap.className = "admin-wrap";
            $(wrap).append($(data).find(".sched-wrap"));
            $("body").append($(data).filter("#event-bar"));
            // Hide the content until fully loaded
            $(wrap).hide();
            // Get admin view js and run it
            $.when($.getScript("/static/confla/timetable.js")).done(function () {
                timetableEdit();
                $(".toggler").trigger("click");
                $(".fa-spinner").remove();
                $(".admin-wrap").show();
            });

            $(content).append(wrap);
        })
    }
}

function getUserSched() {
    var that = this;
    confirm().then(function (answer) {
        if (answer != "cancel") {
            $("#sched-tabs").find("li.active").removeClass("active");
            $("#tab-usersched").off("click");
            $("#tab-usersched").parent().addClass("active");
            $("#event-bar").hide();
            $(".edit-btns").hide();
            $(".admin-wrap").hide();
            spinner = '<i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i>';
            $("body > .container:not(.event-bar)").parent().append(spinner);
            // Save the schedule and wait until it finishes
            // TODO: Better use .then() when checking failstates later
            if (answer == "yes") {
                $.when(timetableSubmit(".table")).done(function (){
                    loadUserview();
                });
            } else {
                loadUserview();
            }
        };
    });
}

function user_setup() {
    userPopoverInit();

    // Delete empty rooms
    $(".table").each(function() {
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
    // Setup nav tabs
    $("#tab-adminsched").click(showAdminsched);
    $("#tab-confsched").click(showRoomConfig);

    user_setup();

    // Close all popovers if clicked outside of a popover or an event
    sel = ".user-wrap .item";
    $('html').on('click', function(e) {
        // If the target is not an event or topic
        if (!$(e.target).hasClass("event-visible") && !$(e.target).hasClass("topic")
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

})
