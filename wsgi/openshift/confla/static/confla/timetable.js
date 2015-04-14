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
        // \||/
        //  \/
        //  |    ALERT!!! We are counting with + 10 minutes, but that may vary!!
        //  O
        secondpart = parseInt(secondpart)+10;
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

$(document).ready(function() {
    var timeslotCount = 0;

    // TODO: The following needs to get row information and count endtime same as
    // seen below
    $(".item").resizable({
        grid: 31,
        containment: "tbody",
        handes: "s",
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
        $(elem).append('<span class="start">Starts at:' + timestart + '</span>');
        var endspan = document.createElement('span');
        endspan.className = "end";
        $(endspan).append("Ends at:" + countEndtime(tr_array, row+1));
        $(elem).append(endspan);

        $(remove).click(function() {
            $(this).closest(".item").remove()
        });

        $(elem).resizable({
            grid: 31,     // size of table cell
            containment: "tbody",
            handles: "s",   // a bug in jQuery does not allow north resize with containment
            resize: function(event, ui) {
                var height = $(this).height();
                var rowdiff = (height-26)/31;
                var endtime_text = countEndtime(tr_array, row+rowdiff+1)
                $(endspan).text("Ends at: " + endtime_text);
            }
        });
        $(this).append(elem);
    })
})
