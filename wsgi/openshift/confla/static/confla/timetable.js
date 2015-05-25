/*
    @file: timetable.js
    @author: Stanislav Laznicka <slaz@seznam.cz>
*/

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

function timetableSubmit(selector) {
    var toSend = timetableToJson(selector);
    $.post("saveTable/", {
        csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
        data: toSend});
}

$(document).ready(function() {
    var timeslotCount = 0;
    var cellSize = 31;

    // Go through all .item objects and make them the right size and resizable
    $(".item").height(function(){
        var len = $(this).attr("deltalen")-1;
        return this.clientHeight+cellSize*len
    }).resizable({
        grid: cellSize,
        containment: "tbody",
        handles: "s",
        resize: function(event, ui) {
            
            var row = $(this).parent().parent().parent().parent().children().index($(this).parent().parent().parent());
            var height = $(this).height();
            var rowdiff = (height-26)/cellSize;
            var endspan = $(this).find("span.end")
            var tr_array = $(this).parent().parent().parent().parent().find('tr');
            var endtime_text = countEndtime(tr_array, row+rowdiff+1)
            $(endspan).text("Ends at: " + endtime_text);
        }
    }).find("div.removesign").click(function() {
            // add closing functionality
            $(this).closest(".item").remove()
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
        $(elem).css({position: "absolute", top: "0", left: "0"});
        var remove = document.createElement('div');
        remove.className="removesign";
        $(remove).append('<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>');
        $(elem).append(remove);
        $(elem).append('<span class="start">Starts at: ' + timestart + '</span>');
        var endspan = document.createElement('span');
        endspan.className = "end";
        $(endspan).append("Ends at:" + countEndtime(tr_array, row+1));
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
        });
        $(this).append(elem);
    })
})
