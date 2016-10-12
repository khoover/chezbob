JSON_SOURCE = "json/shame.json";
JSON_UPDATE_INTERVAL = 10000;
//SCREEN_UPDATE_INTERVAL = 10000;

var shame = [];
var current_user = 0;
var minimum;

var BOX_SELECTORS = [
    "#loading",
    "#all_clear",
    "#balance_box",
    "#time_box",
]

function activate_box(box_selector) {
    for (var i = 0; i < BOX_SELECTORS.length; i++) {
        $(BOX_SELECTORS[i]).css("display", "none");
    }
    $(box_selector).css("display", "block");
    console.log("Activating " + box_selector);
}

function update_page(name, amount) {
    $("#users-name").text(name);
    $("#amount").text("$" + amount);
}

function update_data(on_complete) {
    // This is a closure with on_complete, so needs to be nested.
    function data_update_callback(data, textStatus, jqXHR) {
        console.log("Received updated data...");
        old_shame_length = shame.length;
        shame = data.debtors;
        threshold = data.threshold;

        if (shame.length == 0) {
            // Update the pretty-printed box
            //$("#balance_threshold").text(data.threshold);

            activate_box("#all_clear");
            console.log("All clear!");
        }
        else {
            console.log("Found shameful people.");
            // Fun fact: the ancient version of chromium in 12.04's
            // repos (... we should really upgrade) doesn't support
            // the => syntax sugar.
            function first(x) { return x[1]; }
            function min(x, y) { return Math.min(x, y); }
            minimum = shame.map(first).reduce(min);
            console.log("New minimum: " + minimum);

            if (old_shame_length == 0) {
                choose_someone();
            }

            activate_box("#balance_box");
        }

        if (on_complete != null) {
            on_complete();
        }
    }

    $.getJSON(JSON_SOURCE, "").done(data_update_callback);
}

function choose_someone() {
    var choice = shame[current_user];
    current_user = (current_user + 1) % shame.length;
    //var choice = shame[Math.floor(Math.random()*shame.length)];

    if (choice != null) {
        update_page(choice[0], choice[1]);
        delay = 5000 + (choice[1] - minimum) * 500;
        setTimeout(choose_someone, delay);
        console.log("Switching from " + choice[0] + " in " + delay + " ms");
    }
    else {
        setTimeout(choose_someone, 1000);
    }
}

function start() {
    console.log("Starting...");

    update_data();
    //setInterval(choose_someone, SCREEN_UPDATE_INTERVAL);
    setInterval(update_data, JSON_UPDATE_INTERVAL);
}

$(start);
