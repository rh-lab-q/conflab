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
                    cell["id"] = $(this).find("div.item").attr("id");
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

function timetableDisable() {
    // disable resize, drag and remove removal icon from timeslots
    $(".item").resizable("disable").draggable("disable").find("div.removesign").remove();

    // Remove display: block
    $(".ui-resizable-handle").css('display', '');
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

    $("td").off("dblclick", ".wrap");
}

function timetableEdit() {
    $(".save").show();
    $(".edit").hide();

    // Go through all .item objects and make them resizable and deletable
    $(".item").resizable({
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
        revert: "invalid",
        containment: ".table",
        cursor: "move",
        cursorAt: { top: 20},
        opacity: 0.7,
    }).each(function(){
        // add remove icon to existing timeslots
        var remove = document.createElement('div');
        remove.className="removesign";
        $(remove).append('<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>');
        $(this).prepend(remove);
    }).find("div.removesign").click(function() {
        // add closing functionality
        $(this).closest(".item").remove();
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

    $("td").on("dblclick", ".wrap", function() {
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

        var elem = document.createElement('div');
        elem.className = "item";
        $(elem).attr('id', '0');
        $(elem).css({position: "absolute", top: "0", left: "0"});
        var remove = document.createElement('div');
        remove.className="removesign";
        $(remove).append('<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>');
        $(elem).append(remove);
        $(elem).append('<span class="start" style="display:none">Starts at: ' + timestart + '</span>');
        var endspan = document.createElement('span');
        endspan.className = "end";
        $(endspan).append("Ends at:" + countEndtime(tr_array, row+1)).css('display', 'none');
        $(elem).append(endspan);

        $(remove).click(function() {
            $(this).closest(".item").remove()
        });

        $(elem).resizable({
            grid: cellSize,     // size of table cell
            containment: "tbody",
            handles: "s",   // a bug in jQuery does not allow north resize with containment
            resize: function(event, ui) {
                var height = $(this).height();
                var rowdiff = (height-26)/cellSize;
                var endtime_text = countEndtime(tr_array, row+rowdiff+1)
                $(endspan).text("Ends at: " + endtime_text);
            }
        }).draggable({
            revert: "invalid",
            containment: ".table",
            cursor: "move",
            cursorAt: { top: 20},
            opacity: 0.7,
        });
        $(this).append(elem);
    })

    $(".item").resizable("enable").draggable("enable");
}

$(document).ready(function() {
    var timeslotCount = 0;

    // Bootstrap popover init
    $('[data-toggle="popover"]').each(function() {
        var item = this;
        $(this).popover({
            trigger: "manual",
            placement: "top"
        }).on("mouseenter", function () {
            // Pop on hover and set offset
            var _this = this;
            if ($(this).parent().find(".popover").length == 0) {
                $(this).popover("show");
                $(this).parent().find(".popover").css("top", $(item).height()/2 + "px");
            }
        }).on("mouseleave", function () {
            // Disappear when not hovering over item or popover
            var _this = this;
            setTimeout(function () {
                if (!$(".popover:hover").length) {
                    $(_this).popover("hide");
                }
            }, 300);
        });
    });

    $(".save").hide();

    // Go through all .item objects and make them the right size
    $(".item").height(function(){
        var len = $(this).attr("deltalen")-1;
        return this.clientHeight+cellSize*len
    });

})
