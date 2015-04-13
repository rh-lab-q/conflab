/*
    @file: timetable.js
    @author: Stanislav Laznicka <slaz@seznam.cz>
*/

$(document).ready(function() {
    var timeslotCount = 0;

    $(".item").resizable({
        grid: 31
    });

    $(".wrap").on("dblclick", function() {
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
        $(elem).append("Timeslot " + timeslotCount++);
        $(remove).click(function() {
            $(this).closest(".item").remove()
        });
        $(elem).resizable({
            grid: 31,     // size of table cell
            containment: ".table",
            handles: "s",   // a bug in jQuery does not allow north resize with containment
        });
        $(this).append(elem);
    })
})
