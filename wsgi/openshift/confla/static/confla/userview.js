function changeView() {
    var sel = $(".sel-view option:selected").text();
    switch (sel) {
        case "List": {
            $.get( "/sched/list/", function( data ) {
                $(".sched-wrap:visible").html($(data).find(".schedlist-wrap").html());
                $(".sched-wrap:visible").removeClass().addClass("schedlist-wrap");
            })
            break; 
        };
        case "Grid": {
            $.get( "/sched/", function( data ) {
                $(".schedlist-wrap").html($(data).find(".sched-wrap").html());
                $(".schedlist-wrap").removeClass().addClass("sched-wrap");
            });
            break;
        }
    } 
}
