function changeView() {
    var sel = $(".sel-view option:selected").text();
    switch (sel) {
        case "List": {
            $.get( "list", function( data ) {
                $(".sched-wrap").html($(data).find(".schedlist-wrap").html());
                $(".sched-wrap").removeClass().addClass("schedlist-wrap");
            })
            break; 
        };
        case "Grid": {
            $.get( "", function( data ) {
                $(".schedlist-wrap").html($(data).find(".sched-wrap").html());
                $(".schedlist-wrap").removeClass().addClass("sched-wrap");
            });
            break;
        }
    } 
}
