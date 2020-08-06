
(function() {
    $(document).ready(function() {

        /**
         * The button which triggers the ajax call
         */
        var button = $("#clickme");

        /**
         * Register the click event
         */
        button.click(function() {
            $.ajax({
                url: "comment.html",
                type: "GET"
            }).done(function(response) {
                var text = $(response).filter("#textarea").html();
                $("#content").append("<br/><br/><strong>" + text + "</strong>");
            });
        });

    }); 
})()