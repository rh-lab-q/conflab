/*
    @file: timetable.js
    @author: Stanislav Laznicka <slaz@seznam.cz>
*/

var cellSize = 31;

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

function itemInit(selector) {
    $(selector).resizable({
        grid: cellSize,
        containment: "tbody",
        handles: "s",
        resize: function(event, ui) {
            // New end time on resize
            var row = $(this).parent().parent().parent().parent().children().index($(this).parent().parent().parent());
            var height = $(this).height();
            var rowdiff = (height-26)/cellSize;
            var endspan = $(this).find("span.end")
            var tr_array = $(this).parent().parent().parent().parent().find('tr');
            var endtime_text = countEndtime(tr_array, row+rowdiff+1)
            $(endspan).text("Ends at: " + endtime_text);
        }
    }).draggable({
        handle: "div.movesign",
        revert: "invalid",
        containment: ".table",
        cursorAt: { top: 20},
        opacity: 0.7,
        stack: ".item",
        start: function( event, ui ) {},
        stop: function( event, ui ) {}
    }).droppable({
        accept: ".event",
        tolerance: "pointer",
        hoverClass: "ui-state-hover",
        drop: function( event, ui ) {
            $(ui.draggable).parent().append($(this).find(".event"));
            $(this).append($(ui.draggable));
        }
    }).on("dragstart", function (event, ui) {
        $(ui.helper).find(".movesign").css("cursor", "grabbing");
    }).on("dragstop", function (event, ui) {
        $(ui.helper).find(".movesign").css("cursor", "grab");
    }).find("div.removesign").click(function() {
        // add closing functionality
        $(this).closest(".item").remove();
    });
}

function createSlot(e) {
    if ($(e.target).is("div.wrap") && $(".popover").length === 0) {
        var row = $(this).parent().parent().parent().children().index($(this).parent().parent());
        var timestart = $($(this).parent().parent().children('td')[0]).text();
        // Array of all rows in a table
        var tr_array = $(this).parent().parent().parent().find('tr');

        // A hack so that the text does not get selected on dblclick
        if(document.selection && document.selection.empty) {
            document.selection.empty();
        }
        else if(window.getSelection) {
            var sel = window.getSelection();
            sel.removeAllRanges();
        }

        // Generate timeslot and related HTML objects
        var elem = document.createElement('div');
        elem.className = "item";
        $(elem).attr('slot-id', '0');
        $(elem).css({position: "absolute", top: "0", left: "0"});
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
        var move = document.createElement('div');
        move.className="movesign";
        $(move).append('<span class="glyphicon glyphicon-move"></span>');
        $(buttondiv).append(move);
        $(elem).append(buttondiv);
        $(elem).append('<span class="start" style="display:none">Starts at: ' + timestart + '</span>');
        var endspan = document.createElement('span');
        endspan.className = "end";
        $(endspan).append("Ends at: " + countEndtime(tr_array, row+1)).css('display', 'none');
        $(elem).append(endspan);

        // Generate event
        var nevent = document.createElement('div');
        nevent.className = "event";
        var visevent = document.createElement('div');
        visevent.className = 'event-visible';
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
        $(nform).append($($("[name=csrfmiddlewaretoken]")[0]).clone());
        $(nform).append('<input type="hidden" name="event_id" value="0" />');
        $(nform).append(form);
        $(popcontent).append(nform);
        $(nevent).append(popcontent);
        $(elem).append(nevent);

        // Setup slot removal button
        $(remove).click(function() {
            $(this).closest(".item").remove()
        });
        // Setup jQuery magic for the slot
        itemInit(elem);
        // Setup popover for the slot's event
        popoverInit(edit);
        $(this).append(elem);
    }
}

function timetableToJson(selector) {
    var cols = $(selector + " thead tr th").map(function() {
        return $(this).text()
    });
    var tableObject = $(selector + " tbody tr").map(function(i) {
        var row = {};
        $(this).find('td').each(function(i) {
            if(i > 0) {// omitting the first time-column
                if($(this).text().match(/[a-z]/i)) {// there is actually some text in the cell
                    var rowName = cols[i];
                    var cell = {};
                    // The numbers 10 and 8 are the lenght of "Starts at: ", "Ends at: "
                    cell["start"] = $($(this).find("span.start")).text().slice(11,16);
                    cell["end"] = $($(this).find("span.end")).text().slice(9,14);
                    cell["id"] = $(this).find("div.item").attr("slot-id");
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
    // enable resize, drag and remove removal icon from timeslots
    $(".item").resizable("enable").draggable("enable");
    $(".item-buttons").slideDown();

    // enable event dragging
    $(".event").draggable("enable")

    $(".event-visible").css("cursor", "grab");

    $("td").on("click", ".wrap", createSlot);
}

function timetableDisable() {
    // disable resize, drag and remove removal icon from timeslots
    $(".item").resizable("disable").draggable("disable");
    $(".item-buttons").slideUp();

    // disable event dragging
    $(".event").draggable("disable")

    // Remove display: block
    $(".ui-resizable-handle").css('display', '');

    $(".event-visible").css("cursor", "auto");

    $("td").off("click", ".wrap");
}

function timetableEdit() {
    timetableEnable();
    $(".save").show();
    $(".edit").hide();
}

function timetableSubmit(selector) {
    // generate JSON and submit to DB
    var toSend = timetableToJson(selector);
    $.post("saveTable/", {
        csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
        data: toSend});

    timetableDisable();
    $(".save").hide();
    $(".edit").show();

}

function popoverInit(selector) {
    $(selector).popover({
        placement: "left",
        container: "body",
        html: "true",
        title: function () {
            return $(this).parent().parent().find(".pop-title").html();
        },
        content: function () {
           return $(this).parent().parent().find(".pop-content").html();
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
        var original = $(this).parent().parent().find(".pop-content");
        var popoverSelector = "#" + $(this).attr("aria-describedby");
        var content = $(popoverSelector).find(".popover-content");
        var visible = $(this).parent().parent().find(".event");
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
                form.find("[name=event_id]").attr("value", response);
            }
        });
    });
}

function timetableInit() {
    // Go through all .item objects and make them resizable, deletable, draggable and droppable
    itemInit(".item");

    // Make all events draggable
    $(".event").draggable({
        revert: "invalid",
        containment: ".table",
        cursor: "grabbing",
        opacity: 0.7,
        stack: ".item",
        appendTo: "body",
        zIndex: 1000,
        cursorAt: { top: 20, left: 20 },
        helper: function () {
            var helper = $(this).find(".event-visible").clone()
            $(helper).height($(this).parent().height()/2);
            $(helper).width($(this).parent().width()/2);
            return helper;
        }
    });

    // Make all .wrap divs droppable
    $(".wrap").droppable({
        accept: ".item",
        tolerance: "pointer",
        hoverClass: "ui-state-hover",
        drop: function( event, ui ) {
            var height = $(ui.draggable).height();
            var row = $(ui.draggable).parent().parent().parent().parent().children().index($(this).parent().parent());
            var rownum = $(ui.draggable).parent().parent().parent().parent().children().length
            var rowdiff = (height-26)/cellSize;

            // Check if the item is not partly outside the table
            if ((rownum - row) > rowdiff) {
                // Append the item to the droppable
                $(this).append($(ui.draggable));

                // Delete all styles but save height
                $(ui.draggable).removeAttr("style").height(height);

                // Setup new start and end times
                var endspan = $(ui.draggable).find("span.end");
                var startspan = $(ui.draggable).find("span.start");
                var tr_array = $(ui.draggable).parent().parent().parent().parent().find('tr');
                var my_tr = $(this).parent().parent();
                var endtime_text = countEndtime(tr_array, row+rowdiff+1)
                $(startspan).text("Starts at: " + $(my_tr.children('td')[0]).text())
                $(endspan).text("Ends at: " + endtime_text);
            }
            else {
                // Revert to original position
                ui.draggable.draggable('option', 'revert', true);
            }
        }
    });

    // Create a new slot
    $("td").on("click", ".wrap", createSlot);
    timetableDisable();
}

$(document).ready(function() {
    var timeslotCount = 0;
    // Bootstrap popover init
    popoverInit(".editsign");

    timetableInit();

    // Close all edit popovers if clicked outside of a popover or edit icon
    $('html').on('click', function(e) {
        if (!$(e.target).parent().hasClass("editsign")
            && $(e.target).parents('.popover.in').length === 0) {
                $('.editsign').each( function () {
                // If there is an open popover, hide it
                if ($(this).attr("aria-describedby")) {
                   $(this).popover('hide');
                }
            });
        }
    });
    $(".save").hide();

    // Go through all .item objects and make them the right size
    $(".item").height(function(){
        var len = $(this).attr("deltalen")-1;
        return this.clientHeight+cellSize*len
    });
})
