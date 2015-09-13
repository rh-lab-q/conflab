function show_error(name, response) {
    $(".fa-spinner").remove();
    // Show Failed to load error message
    var div = '<div class="alert alert-danger">Failed to load ' + name + '. Please try again.</div>';
    $("body > .container:not(#event-bar)").append(div);
    // Show the original error message
    var resp = $(response.responseText);
    $("body > .container:not(#event-bar)").append($(resp).filter("div"));
}

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
            $.when($.get( "/sched/list/")).then(function(response) {
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
            $.when($.get( "/sched/")).then(function(response) {
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

function userPopoverInit() {
    $(".user-wrap .item").each (function () {
        var itemp = this;
        var mousepos = {top: 0, left: 0, height: 0, width: 0};
        var arrowsize = 11; // arrow size in pixels
        $(itemp).click(function(e){
            mousepos.top = e.pageY;
            mousepos.left = e.pageX;
        }).popover({
            placement: "auto bottom",
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

function showUsersched() {
    $("[aria-describedby]").popover("hide");
    if ($(".active > a", "#sched-tabs").is("#tab-adminsched")) {
        // Went from adminsched to usersched
        // Show save dialog
        confirm().then(function (answer) {
            if (answer != "cancel") {
                $(".alert").remove();
                $("#sched-tabs").find("li.active").removeClass("active");
                $("#tab-usersched").off("click");
                $("#tab-usersched").parent().addClass("active");
                $("#event-bar").hide();
                $(".edit-btns").hide();
                $(".admin-wrap").hide();
                spinner = '<div class="spinnerwrap"><i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i></div>';
                $("body > .container:not(#event-bar)").parent().append(spinner);
                // Save the schedule and wait until it finishes
                if (answer == "yes") {
                    $.when(timetableSubmit(".table")).then(function (){
                        // Success
                        getUserSched();
                    }, function (response){
                        // Failure
                        var div = '<div class="alert alert-danger">Failed to save schedule. Please try again.</div>';
                        $(".admin-wrap").prepend(div);
                        // Rollback changes to the view
                        $("#sched-tabs").find("li.active").removeClass("active");
                        $("#tab-adminsched").parent().addClass("active");
                        $("#event-bar").show();
                        $(".admin-wrap").show();
                        $("#tab-usersched").off("click").click(showUsersched);
                        $(".fa-spinner").remove();
                    });
                } else {
                    getUserSched();
                }
            };
        });
        $("#tab-adminsched").off("click").click(showAdminsched);
    } else if ($(".active > a", "#sched-tabs").is("#tab-roomconf")) {
        // Went from roomconf to usersched
        $("#tab-usersched").off("click");
        $("#tab-roomconf").off("click").click(showRoomConfig);
        $("#sched-tabs").find("li.active").removeClass("active");
        $("#tab-usersched").off("click");
        $("#tab-usersched").parent().addClass("active");
        $(".config-wrap").remove();
        spinner = '<div class="spinnerwrap"><i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i></div>';
        $("body > .container:not(#event-bar)").parent().append(spinner);
        getUserSched();
        $("#sched-tabs").find("li.active").removeClass("active");
        $(this).parent().addClass("active");
    }
}

function showAdminsched() {
    $("[aria-describedby]").popover("hide");
    $(".alert").remove();
    $("#tab-adminsched").off("click");
    if ($(".active > a", "#sched-tabs").is("#tab-usersched")) {
        // Went from usersched to adminsched
        $(".user-wrap").remove();
        getAdminSched();
        $("#tab-usersched").off("click").click(showUsersched);
    } else if ($(".active > a", "#sched-tabs").is("#tab-roomconf")) {
        // Went from roomconf to adminsched
        $(".config-wrap").remove();
        getAdminSched();
        $("#tab-roomconf").off("click").click(showRoomConfig);
    }
    $("#sched-tabs").find("li.active").removeClass("active");
    $(this).parent().addClass("active");
}

function showRoomConfig() {
    $("[aria-describedby]").popover("hide");
    if ($(".active > a", "#sched-tabs").is("#tab-adminsched")) {
        // Went from adminsched to roomconf
        // Show save dialog
        confirm().then(function (answer) {
            if (answer != "cancel") {
                $(".alert").remove();
                $("#sched-tabs").find("li.active").removeClass("active");
                $("#tab-roomconf").off("click");
                $("#tab-roomconf").parent().addClass("active");
                $("#event-bar").hide();
                $(".edit-btns").hide();
                $(".admin-wrap").hide();
                spinner = '<div class="spinnerwrap"><i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i></div>';
                $("body > .container:not(#event-bar)").parent().append(spinner);
                // Save the schedule and wait until it finishes
                if (answer == "yes") {
                    $.when(timetableSubmit(".table")).then(function (){
                            // Success
                            getRoomConfig();
                        }, function (response){
                            // Failure
                            var div = '<div class="alert alert-danger">Failed to save schedule. Please try again.</div>';
                            $(".admin-wrap").prepend(div);
                            // Rollback changes to the view
                            $("#sched-tabs").find("li.active").removeClass("active");
                            $("#tab-adminsched").parent().addClass("active");
                            $("#event-bar").show();
                            $(".admin-wrap").show();
                            $("#tab-usersched").off("click").click(showUsersched);
                            $(".fa-spinner").remove();
                        });
                } else {
                    getRoomConfig();
                }
            };
        });
        $("#tab-adminsched").off("click").click(showAdminsched);
    } else if ($(".active > a", "#sched-tabs").is("#tab-usersched")) {
        // Went from usersched to roomconf
        $(".user-wrap").remove();
        getRoomConfig();
        $("#tab-roomconf").off("click");
        $("#tab-usersched").off("click").click(showUsersched);
        $("#sched-tabs").find("li.active").removeClass("active");
        $(this).parent().addClass("active");
    }
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
        content = $("body > .container:not(#event-bar)");
        spinner = '<div class="spinnerwrap"><i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i></div>';
        $(".user-wrap").remove();
        $(content).append(spinner);
        $.when($.get(edit_link)).then(function (response) {
            // Success
            var wrap = document.createElement('div');
            wrap.className = "admin-wrap";
            $(wrap).append($(response).find(".sched-wrap"));
            $("body").append($(response).filter("#event-bar"));
            // Hide the content until fully loaded
            $(wrap).hide();
            // TODO: More error checking?
            $.getScript("/static/confla/eventedit.js");
            // Get admin view js and run it
            $.when($.getScript("/static/confla/timetable.js")).then(function (response) {
                // Success
                timetableEdit();
                $(".toggler").trigger("click");
                $(".fa-spinner").remove();
                $(".admin-wrap").show();
            }, function (response) {
                // Failure
                show_error("schedule editor", response);
            });

            $(content).append(wrap);
        }, function (response){
            // Failure
            show_error("schedule editor", response);
        });
    }
}

function getUserSched() {
    $.when($.get(user_link)).then(function(response) {
        // Success
        var wrap = document.createElement('div');
        wrap.className = "user-wrap";
        $(wrap).append($(response).find(".display-style"));
        $(wrap).append($(response).find(".sched-wrap"));
        $(wrap).hide();
        $("body > .container:not(#event-bar)").append(wrap);
        user_setup();
        $(".fa-spinner").remove();
        $(wrap).show();
    }, function (response){
        // Failure
        show_error("schedule", response);
    });
}

function getRoomConfig() {
    content = $("body > .container:not(#event-bar)");
    $.when($.get(config_link)).then(function(response) {
        // Success
        var wrap = document.createElement('div');
        wrap.className = "config-wrap";
        $(wrap).append($(response).find("#slot_edit"));
        // Hide the content until fully loaded
        $(wrap).hide();
        // Get admin view js and run it
        $.when($.getScript("/static/confla/edit_slot.js")).then(function () {
            $(".config-wrap").show();
            selectize_setup(".fieldset-content:visible .room-select");
        }, function (response){
            // Failure
            show_error("configuration", response);
        });
        $(".fa-spinner").remove();
        $(content).append(wrap);
    }, function (response){
        // Failure
        show_error("configuration", response);
    });
}

function user_setup() {
    userPopoverInit();

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
    $("#tab-roomconf").click(showRoomConfig);

    user_setup();
})
