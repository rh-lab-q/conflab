function changeView() {
    var sel = $(".sel-view option:selected").text();
    switch (sel) {
        case "List": {
            $.get( "/sched/list/", function( data ) {
                $(".sched-wrap:visible").html($(data).find(".schedlist-wrap").html());
                $(".sched-wrap:visible").removeClass().addClass("schedlist-wrap");
                popoverInit();
            })
            break; 
        };
        case "Grid": {
            $.get( "/sched/", function( data ) {
                $(".schedlist-wrap").html($(data).find(".sched-wrap").html());
                $(".schedlist-wrap").removeClass().addClass("sched-wrap");
                popoverInit();
            });
            break;
        }
    } 
}

function popoverInit() {
    $(".item").popover({
        placement: "bottom",
        html: "true",
        title: " ",
        content: function () {
            var itemp = this;
            spinner = '<i style="text-align:center" class="fa fa-5x fa-spinner fa-spin"></i>';
            def = $.post("/events/popover/", {
                csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
                data: $(".event", this).attr("event-id"),
            });
            // TODO: Better use .then() when checking failstates later
            $.when(def).done(function (response){
                var popid = "#" + $(itemp).attr("aria-describedby");
                $(popid).find(".fa-spinner").remove();
                $(popid).find(".popover-content").append(response);
            });
            return spinner;
        }
    });
}

$(document).ready(function() {
    popoverInit();
})
