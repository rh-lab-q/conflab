/*
    @file: timetable.js
    @author: Stanislav Laznicka <slaz@seznam.cz>
    @author: Petr Kubat <petr.kubat.hb@seznam.cz>
*/

var cellSize = 30;
var itemHeight = 28;
$.expr[':'].Contains = function(a, i, m) {
    // m is PROBABLY an array ofcCaller, calling method('Contains'), and content of the call
    return (a.textContent || a.innerText || "").toUpperCase().indexOf(m[3].toUpperCase()) >= 0;
}

function listFilter(input, list, elem) {
    $(input)
        .change(function() {
            var filter = $(this).val();
            if(filter) {
                $matches = $(list).find(elem + ':Contains(' + filter + ')').parent();
                $('.event-visible', list).not($matches).hide();
                $matches.show();
            }
            else {
                $(list).find('.event-visible').show();
            }
            return false;
        })

        .keyup(function() {
            $(this).change();
        });
}

function countEndtime(tr_array, rownumber) {
    /*
        Function that gets the endtime of a timeslot
        from the given rownumber. If the rownumber is too
        big, it counts the last time that's not in the table.

        WARNING: Time has to be in the first cell on each row
    */
    if(rownumber === tr_array.length) {
        var time_td = $(tr_array[tr_array.length-1]).children('td')[0];
        var td_text = $(time_td).text();
        var firstpart = td_text.slice(0,2);
        var secondpart = td_text.slice(3,5);
        var tdelta = $(tr_array).parent().parent().attr("tdelta")
        secondpart = parseInt(secondpart)+parseInt(tdelta);
        if(secondpart >= 60) {
            firstpart = parseInt(firstpart) + 1;
            secondpart = secondpart - 60;
            if(secondpart === 0) secondpart = "00";
        }
        var endtime_text = firstpart + ':' + secondpart;
    }
    else {
        var endtime = $(tr_array[rownumber]).children('td')[0];
        var endtime_text = $(endtime).text();
    }

    return endtime_text;
}

function eventInit(selector) {
    $(selector).each( function() {
        $(this).draggable({
            revert: "invalid",
            containment: "body",
            cursor: "grabbing",
            opacity: 0.7,
            //stack: ".item",
            appendTo: "body",
            zIndex: 10000,
            cursorAt: { top: 20, left: 20 },
            helper: function () {
                var helper = $(this).find(".event-visible").clone();
                $(helper).height(50);
                $(helper).width($(this).parent().width()/2);
                return helper;
            }
        }).find("div.removesign").click(function() {
            // add closing functionality
            $(this).closest(".item").addClass("empty").resizable("destroy");
            $(this).closest(".wrap").droppable("destroy");
            emptyItemInit($(this).closest(".item"));
            $(this).closest(".event").remove();
        });
        $(this).find(".event-visible").css("cursor", "grab");
        if ($(this).find(".topic").text()) {
            // Setup primary tag in tag select
            $(this).find(".event-visible").each(function () {
                tagId = $(this)[0].className.split(/\s+/)[1].slice(3);
                if (tagId) {
                    select = $(this).parent().find(".sel-tag");
                    select.prepend($(select).find("[value=" + tagId + "]"));
                }
            });
        }
    });
    $(selector).closest("td").off("click");
}

function itemInit(selector) {
    $(selector).resizable({
        grid: cellSize,
        containment: "tbody",
        handles: "s",
        resize: function(event, ui) {
            // New end time on resize
            var row = $(this).parent().parent().parent().parent().children().index($(this).parent().parent().parent());
            var height = $(this).height();
            var rowdiff = (height-itemHeight)/cellSize;
            var endspan = $(this).find("span.end")
            var tr_array = $(this).parent().parent().parent().parent().find('tr');
            var endtime_text = countEndtime(tr_array, row+rowdiff+1)
            $(endspan).text("Ends at: " + endtime_text);
        }
    })
    // Setup wrap as the droppable
    $(selector).parent().droppable({
        accept: ".event",
        tolerance: "pointer",
        drop: function( event, ui ) {
            item = $(this).find(".item");
            // Dont drop into itself
            if (!$(item).is($(ui.draggable).parent())) {
                // Don't append empty events to event list
                if ($(ui.draggable).parent().is("#event-list") &&
                        !$(item).find(".topic:hidden").text()) {
                    $(item).find(".event").remove();
                    $(item).append($(ui.draggable));
                }
                else if ($(ui.draggable).parent().is("#event-list")) {
                    // Dragged from event list
                    $(ui.draggable).parent().append($(item).find(".event:hidden").show());
                    $(item).find(".drag-help").remove();
                    $(item).append($(ui.draggable));
                } else {
                    // Dragged from a different item
                    $(item).find(".drag-help").remove();
                    $(ui.draggable).parent().find(".drag-help").remove();
                    $(ui.draggable).parent().append($(item).find(".event").show());
                    $(item).append($(ui.draggable).show());
                }
            }
        },
        over: function(event, ui) {
            var item = $(this).find(".item");
            // Ignore over event from yourself
            if (!$(item).is($(ui.draggable).parent())) {
                // Ensure the code is run after out finishes
                setTimeout(function () {
                    if (!$(ui.draggable).parent().is("#event-list")) {
                        // Dragged from a different item
                        if (!$(item).is($(ui.draggable).parent())) {
                            // Dragged over a different item
                            $(ui.draggable).parent().append($(item).find(".event").clone().addClass("drag-help").show());
                            $(item).find(".event").hide();
                            $(item).append($(ui.draggable).clone().addClass("drag-help").show());
                            $(ui.draggable).hide();
                        }
                    }
                    else {
                        // Dragged from event list
                        $(item).find(".event").hide();
                        $(item).append($(ui.draggable).clone().addClass("drag-help"));
                    }
                }, 0);
            }
        },
        out: function(event, ui) {
            item = $(this).find(".item");
            if (!$(ui.draggable).parent().is("#event-list")) {
                // Dragged from a different item
                if (!$(item).is($(ui.draggable).parent())) {
                    // Dragged out of a different item
                    $(".event:hidden").show(); //ui.draggable
                    $(".drag-help").remove();
                    //$(item).find(".event").show();
                }
            }
            else {
                // Dragged from event list
                $(item).find(".drag-help").remove();
                $(item).find(".event").show();
            }
        }
    }).on("dragstart", function (event, ui) {
        $(ui.helper).find(".movesign").css("cursor", "grabbing");
    }).on("dragstop", function (event, ui) {
        $(ui.helper).find(".movesign").css("cursor", "grab");
    });
}

function emptyItemInit(selector) {
    $(selector).parent().droppable({
        accept: ".event",
        tolerance: "pointer",
        drop: function( event, ui ) {
            var item = $(this).find(".item");
            // Dont drop into itself
            if (!$(item).is($(ui.draggable).parent())) {
                if (!$(ui.draggable).parent().is("#event-list")) {
                    // Dragged from a different item
                    var slot = $(ui.draggable).parent();
                    slot.addClass("empty");
                    slot.resizable("destroy");
                    slot.parent().droppable("destroy");
                    emptyItemInit(slot);
                }
                $(item).find(".drag-help").remove();
                $(item).append($(ui.draggable).show());
                $(item).removeClass("empty");
                itemInit(item);
            }
        },
        over: function(event, ui) {
            var item = $(this).find(".item");
            // Ignore over event from yourself
            if (!$(item).is($(ui.draggable).parent())) {
                // Ensure the code is run after out finishes
                setTimeout(function () {
                    if (!$(ui.draggable).parent().is("#event-list")) {
                        // Dragged from a different item
                        $(ui.draggable).parent().addClass("empty");
                        if (!$(item).is($(ui.draggable).parent())) {
                            // Dragged over a different item
                            $(item).append($(ui.draggable).clone().addClass("drag-help"));
                            $(ui.draggable).hide();
                        }
                    }
                    else {
                        // Dragged from event list
                        $(item).append($(ui.draggable).clone().addClass("drag-help"));
                    }
                    //$(item).removeClass("empty");
                }, 0);
            }
        },
        out: function(event, ui) {
            var item = $(this).find(".item");
            if (!$(ui.draggable).parent().is("#event-list")) {
                $(ui.draggable).parent().removeClass("empty");
                // Dragged from a different item
                if (!$(item).is($(ui.draggable).parent())) {
                    // Dragged out of a different item
                    $(".drag-help").remove();
                    $(".event:hidden").show();
                }
            }
            else {
                // Dragged from event list
                $(item).find(".drag-help").remove();
            }
            //$(item).addClass("empty");
        }
    });
    $(selector).closest("td").off("click").on("click", ".item", appendEvent);
}

function createEvent() {
        var nevent = document.createElement('div');
        nevent.className = "event";
        var visevent = document.createElement('div');
        visevent.className = 'event-visible tag0';
        var buttondiv = document.createElement('div');
        buttondiv.className="item-buttons";
        var remove = document.createElement('div');
        remove.className="removesign";
        $(remove).append('<span class="glyphicon glyphicon-remove"></span>');
        $(buttondiv).append(remove);
        var edit = document.createElement('div');
        edit.className="editsign";
        $(edit).append('<span class="glyphicon glyphicon-edit"></span>');
        $(buttondiv).append(edit);
        $(visevent).append(buttondiv); 
        $(visevent).append('<p class="topic"></p>');
        $(visevent).append('<p class="author"></p>');
        $(nevent).append(visevent);
        // Generate popover title and content
        var poptitle = document.createElement('div');
        poptitle.className = "pop-title";
        $(poptitle).attr("style", "display : none");
        // TODO: Translation in javascript
        // https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#using-the-javascript-translation-catalog
        $(poptitle).append('<span>Add event</span>')
        $(poptitle).append('<span class="pop-close" glyphicon glyphicon-remove></span>');
        $(nevent).append(poptitle);
        var popcontent = document.createElement('div');
        popcontent.className = "pop-content";
        $(popcontent).attr("style", "display : none");
        // Event create form
        nform = document.createElement('form');
        $(nform).attr("method", "post");
        $(nform).attr("action", form_action);
        $(nform).append($($("[name=csrfmiddlewaretoken]")[0]).clone());
        $(nform).append('<input type="hidden" name="event_id" value="0" />');
        $(nform).append(form);
        $(popcontent).append(nform);
        $(nevent).append(popcontent);
        // jQuery magic
        popoverInit(edit);
        eventInit(nevent);
        return nevent;
}

function appendEvent(e) {
    var wrap = $(this).parent();
    $(this).removeClass("empty");
    var newevent = createEvent();
    $(wrap).droppable("destroy");
    itemInit(this);
    $(this).append(newevent);
    $(this).closest("td").off("click");
}

function timetableToJson(selector) {
    var cols = $(selector + " thead tr th").map(function() {
        return $(this).text()
    });
    var tableObject = $(selector + " tbody tr").map(function(i) {
        var row = {};
        $(this).find('td').each(function(i) {
            if(i > 0) {// omitting the first time-column
                if($(this).text().match(/[a-z]/i) // there is actually some text in the cell
                   && $(this).find(".event").length != 0) { // there is an event inside the cell
                    var rowName = cols[i];
                    var cell = {};
                    // The numbers 10 and 8 are the lenght of "Starts at: ", "Ends at: "
                    cell["day"] = $(this).closest(".day-wrap").find("h4").text()
                    cell["start"] = $($(this).find("span.start")).text().slice(11,16);
                    cell["end"] = $($(this).find("span.end")).text().slice(9,14);
                    cell["event"] = $(this).find("[name=event_id]").attr("value")
                    row[rowName] = cell;
                }
            }
        });
        return row;
    }).get()
    for(i = 0; i < tableObject.length; i++) {
        if(Object.getOwnPropertyNames(tableObject[i]).length === 0) {
            tableObject.splice(i, 1);
            i--;
        }
    }

    return JSON.stringify(tableObject);
}

function timetableEnable() {
    // enable resize
    $(".item:not(.empty)").resizable("enable");

    // enable event dragging for nonempty events
    $(".event").each( function() {
        if ($(this).find(".topic").text()) {
            $(this).draggable("enable")
        }
    });

    $(".event-visible").css("cursor", "grab");
}

function timetableDisable() {
    // disable resize
    $(".item:not(.empty)").resizable("disable");

    // disable event dragging
    $(".event").draggable("disable")

    // Remove display: block
    $(".ui-resizable-handle").css('display', '');

    $(".event-visible").css("cursor", "auto");
}

function timetableEdit() {
    timetableEnable();
    $(".save").show();
    $(".edit").hide();
    $("#event-bar").show();
}

function timetableSubmit(selector) {
    // generate JSON and submit to DB
    var toSend = timetableToJson(selector);
    def = $.post("/admin/sched/saveTable/", {
        csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
        data: toSend});

    timetableDisable();
    $(".save").hide();
    $(".edit").show();
    $("#event-bar").hide();
    return def;
}

function popoverInit(selector) {
    $(selector).popover({
        placement: "left",
        container: "body",
        html: "true",
        title: function () {
            console.log($(this).parent().parent().parent());
            return $(this).parent().parent().parent().find(".pop-title").html();
        },
        content: function () {
           return $(this).parent().parent().parent().find(".pop-content").html();
        }
    }).on("shown.bs.popover", function() {
        // Set click method for the close icon
        var item = this;
        var popoverSelector = "#" + $(this).attr("aria-describedby");
        $(popoverSelector).find(".pop-close").on("click", function () {
            $(item).popover("hide");
        });

        // Selectize speaker init
        $(".popover").find(".sel-speaker").each( function () {
            var select = this;
            var itemlist = [];
            $(this).find("[selected='selected']").each(function () {
                itemlist.push($(this).text());
            });
            $(this).selectize({
                persist: false,
                maxItems: null,
                valueField: 'username',
                labelField: 'name',
                searchField: ['name', 'username'],
                options: users,
                items: itemlist,
                render: {
                    item: function(item, escape) {
                        return '<div>' +
                            (item.name ? '<span class="name">' + escape(item.name) + ' </span>' : '') +
                            (item.username ? '<span class="username">(' + escape(item.username) + ')</span>' : '') +
                        '</div>';
                    },
                    option: function(item, escape) {
                        var label = item.username;
                        var caption = item.name;
                        return '<div>' +
                            '<span class="label">' + escape(label) + '</span>' +
                            (caption ? '<span class="caption">' + escape(caption) + '</span>' : '') +
                        '</div>';
                    }
                }
            });
            $("div.sel-speaker").removeClass("selectize-input");
        });

        // Selectize tags init
            $(".popover").find(".sel-tag").each( function () {
                var select = this;
                var itemlist = [];
                $(this).find("[selected='selected']").each(function () {
                    itemlist.push($(this).val());
            });
            $(this).selectize({
                plugins: ['drag_drop'],
                persist: false,
                maxItems: null,
                valueField: 'id',
                labelField: 'name',
                searchField: ['name'],
                //options: users,
                items: itemlist,
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
            $("div.sel-tag").removeClass("selectize-input");
        });
    }).on("hide.bs.popover", function () {
        var original = $(this).parent().parent().parent().find(".pop-content");
        var popoverSelector = "#" + $(this).attr("aria-describedby");
        var content = $(popoverSelector).find(".popover-content");
        var visible = $(this).parent().parent();
        var selSpeaker = $(content).find("select.sel-speaker");
        var selTag = $(content).find("select.sel-tag");

        // Copy edited content into original html
        $(original).find("#id_topic").attr("value", ($(content).find("#id_topic").val()));
        $(original).find("#id_description").text($(content).find("#id_description").val());
        $(visible).find(".topic").text(($(content).find("#id_topic").val()));
        $(visible).find(".desc").text($(content).find("#id_description").val());
        // Go through all options in the original selects and mark them selected/not selected
        // TODO: Add the values to visible event

        // Speaker select
        $(original).find("select.sel-speaker").children().each(function () {
            if ($.inArray($(this).text(), selSpeaker[0].selectize.items) !== -1) {
                $(this).attr("selected", "selected");
            }
            else {
                $(this).removeAttr("selected");
            }
        });

        var items = selTag[0].selectize.items;
        // Move the primary tag to the correct place
        tagId = items[0];
        if (tagId) {
            select = $(original).find(".sel-tag");
            select.prepend($(select).find("[value=" + tagId + "]"));
        }
        // Setup correct css class for the tag
        $(original).parent().find(".event-visible")[0].className = "event-visible tag" + tagId;
        // Tag select
        $(original).find("select.sel-tag").children().each(function () {
            if ($.inArray($(this).val(), selTag[0].selectize.items) !== -1) {
                $(this).attr("selected", "selected");
            }
            else {
                $(this).removeAttr("selected");
            }
        });
        // Save the event form
        var form = original.find("form");
        $(form).ajaxForm();
        $(form).ajaxSubmit({
            success: function(response) {
                var event_id = form.find("[name=event_id]");
                if (event_id.attr("value") == 0 && response !== "-1") {
                    event_id.attr("value", response);
                }
            }
        });
        // TODO: Check response before enabling
        $(original).parent().draggable("enable");
        $(original).parent().find(".event-visible").css("cursor", "grab");
    });
}

function timetableInit() {
// Go through all .item objects and make them resizable and droppable
itemInit(".item:not(.empty)");
// Make all empty items droppable
emptyItemInit(".item.empty");

// Make all events draggable
eventInit(".event");

timetableDisable();
}

$(document).ready(function() {
    // Go through all .item objects and make them the right size
    $(".item").height(function(){
        var len = $(this).attr("deltalen");
        if (len == "default") len = 1;
        return this.clientHeight+cellSize*len
    });

    // Setup BootSideMenu
    $('#event-bar').BootSideMenu({
        side: "right",
        autoClose: true // on page load
    });

    // Bootstrap popover init
    popoverInit(".editsign");
    // Timetable jQuery init
    timetableInit();

    $("#event-bar").droppable({
        greedy: true,
        accept: ".event",
        tolerance: "pointer",
        //hoverClass: "ui-state-hover",
        drop: function(event, ui) {
            // Don't append empty events to event list
            if (!$(ui.draggable).parent().is("#event-list")) {
                var nevent = createEvent();
                $(ui.draggable).parent().append(nevent);
            }
            $(this).find("#event-list").append($(ui.draggable).show());
            $("#filter_input").change();
            $(".item").droppable("enable");
        },
        over: function(event, ui) {
            $(".item").droppable("disable");
            // Remove drag helpers from all items and show original events
            $(".drag-help").parent().find(".event").show();
            $(".drag-help").remove();
            // Then hide the dragged event
            $(ui.draggable).hide();
        },
        out: function(event, ui) {
            $(".item").droppable("enable");
            $(ui.draggable).show();
        }
    });

    // Close all edit popovers if clicked outside of a popover or edit icon
    $('html').on('click', function(e) {
        // If the target is not the edit icon
        if (!$(e.target).parent().hasClass("editsign")
            // If the target is not a popover
            && $(e.target).parents('.popover.in').length === 0) {
                $('.editsign').each( function () {
                // If there is an open popover, hide it
                if ($(this).attr("aria-describedby")) {
                   $(this).popover('hide');
                }
            });
        }
    });
    listFilter($("#filter_input"), $("#event-list"), "p");

    // Setup slot lengths for empty slots
    that = $(".table:first");
    // For each room name table header except the first one (time)
    $("th:not(:first-child)", that).each(function() {
        var index = $(this).index() + 1;
        var slot_len = $(this).attr("slot_len")
        // Setup the length of every empty slot to the rooms default for each column
        // given by "index"
        $("td:nth-child("+ index +") .empty").closest(".item").each(function() {
            $(this).height(this.clientHeight+cellSize*slot_len);
        });
    });

    // Set up a dummy scrollbar at the top of the table
    $(".table-dummy").width($(".table").width());
    // Propagate scroll events into the proper scrollbar
    $("#dummy-wrap").scroll(function(){
        $("#table-wrap")
            .scrollLeft($("#dummy-wrap").scrollLeft());
    });
    $("#table-wrap").scroll(function(){
        $("#dummy-wrap")
            .scrollLeft($("#table-wrap").scrollLeft());
    });
})
