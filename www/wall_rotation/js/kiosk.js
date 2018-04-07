var JSON_SOURCE = "wall.json";

var UPDATE_INTERVAL = 60000;
var UPDATE_INTERVAL_OBJ = null;

var PAGE_UPDATE_INTERVAL = 300000;
var PAGE_UPDATE_INTERVAL_OBJ = null;

var DEFAULT_SWITCH_INTERVAL = 10000;

var IMAGE_VIEWER = 'image_viewer.html';

var INITIAL_WAIT = 500;
var DEFAULT_DURATION = 30;

var urls = [];

var current_index = 0;
var holding = false;
var tags;
var outstanding_change_request = null;

function array_contains(arr, query) {
    for (var i = 0; i < arr.length; ++i) {
        if (query == arr[i])
            return true;
    }
    return false;
}

function polyfill() {
    if (!String.prototype.endsWith) {
        String.prototype.endsWith = function(
                searchString, position) {
            var subjectString = this.toString();
            if (    typeof position !== 'number' ||
                    !isFinite(position) ||
                    Math.floor(position) !== position ||
                    position > subjectString.length) {
                position = subjectString.length;
            }
            position -= searchString.length;
            var lastIndex = subjectString.lastIndexOf(
                searchString, position);
            return lastIndex !== -1 && lastIndex === position;
        };
    }

    if (!String.prototype.startsWith) {
        String.prototype.startsWith = function(
                searchString, position) {
            position = position || 0;
            return (
                this.substr(position, searchString.length) ===
                searchString);
        };
    }

}

function tagged_log(msg) {
    console.log('%cKiosk> %c' + msg,
                'background: #222; color: #35baea',
                //'background: #222; color: #aada25',
                'background: none; color: default');
}

function init_update_check() {
    function get_headers(cb) {
        $.ajax(
            document.location.href,
            { method: "HEAD", complete: cb }
        );
    }

    var last_updated;

    get_headers(function(resp) {
        last_updated = resp.getResponseHeader("Last-Modified");
    });

    PAGE_UPDATE_INTERVAL_OBJ = setInterval(
        function () {
            tagged_log("Checking for page updates.");
            get_headers(
                function(resp) {
                    if (    last_updated !=
                            resp.getResponseHeader("Last-Modified")) {
                        location.reload();
                    }
                });
        },
        PAGE_UPDATE_INTERVAL);
}

function get_params() {
    var query = location.search.substr(1);
    var result = {};
    query.split("&").forEach(function(part) {
        var item = part.split("=");
        result[item[0]] = decodeURIComponent(item[1]);
    });
    return result;
}

function skip_forward() {
    clearTimeout(outstanding_change_request);
    interval_timer();
}

function update_page_source(details, entry) {
    var forceRefresh = (details.hasOwnProperty("force_refresh") ?
                        details.force_refresh : false);
    var iframe = $("#frame");

    if (forceRefresh || details.url != iframe.attr('src')) {
        tagged_log("Updating src to url: " + details.url);
        if (!insert_image(details)) {
            $("#frame").attr('src', details.url);
        }
        $("#url_id a").text(entry.url_id);
    }
}

function update_iframe_and_set_timeout(details, entry) {
    tagged_log("Updating iframe.");
    tagged_log("Details:" + JSON.stringify(details));
    tagged_log("Entry:" + JSON.stringify(entry));
    if (!details.hasOwnProperty("url")) {
        tagged_log("Skipping blank entry: " +
                    JSON.stringify(details));
        holding = false;
        if (urls.length == 1) {
            outstanding_change_request = setTimeout(
                interval_timer, DEFAULT_SWITCH_INTERVAL);
        }
        else {
            interval_timer();
        }
        return;
    }

    if (details.hasOwnProperty("hold_tags") &&
            array_contains(details.hold_tags, tags)) {
        tagged_log("Hold set.");
        //tagged_log("TEMPORARILY DISABLED");
        holding = true;
    }
    else {
        tagged_log("No hold set.");
        holding = false;
    }

    var duration = (details.hasOwnProperty("duration") ?
                    parseInt(details.duration) : DEFAULT_DURATION);

    update_page_source(details, entry);

    outstanding_change_request = setTimeout(
        interval_timer, duration * 1000);
    tagged_log("Updating in " + duration + " seconds");
}

function weighted_choice(choices) {
    var i;
    var total = 0;
    for (i = 0; i < choices.length; ++i) {
        total += 1.0 / choices[i].duration;
    }

    r = total * Math.random();

    upto = 0;
    for (i = 0; i < choices.length; ++i) {
        weight = 1.0 / choices[i].duration;
        upto += weight;
        if (upto >= r) {
            return i;
        }
    }
}

function get_next_url_index() {
    //return weighted_choice(urls);
    tagged_log("Rotating instead of randomly choosing...");
    return (current_index + 1) % urls.length;
}

function setup_manual_controls() {
    $("#url_id a").on("click", skip_forward);
    $(document).keypress(function(e) {
        if (e.which == 13) { // enter key
            skip_forward();
        }
    });
}

function insert_image(details) {
    tagged_log("Evaluating insert_image on " + JSON.stringify(details));
    if ( details === null ) {
        tagged_log("Error: Null details object for insert_image?");
        return false;
    }

    if ( !details.hasOwnProperty("url") ) {
        return false;
    }

    if ( !details.hasOwnProperty("type") ) {
        details.type = 'unknown';
    }

    if ( details.type != 'image' &&
            (!details.url.endsWith(".jpg") &&
             !details.url.endsWith(".png") &&
             !details.url.endsWith(".gif"))) {
        return false;
    }
    tagged_log("Interpreting as an image");

    var iframe = $("#frame");
    iframe.attr('src', IMAGE_VIEWER);
    iframe.load(function() {
        iframe.contents().find('#img').css(
            {'background-image': 'url(' + details.url + ')'});
        tagged_log("Set background url");
    });
    return true;
}

function interval_timer() {
    tagged_log("Interval timer launched");
    if (urls.length === 0) {
        tagged_log("No URLs to load...");
        outstanding_change_request = setTimeout(
            interval_timer, DEFAULT_SWITCH_INTERVAL);
        return;
    }

    if (!holding) {
        current_index = get_next_url_index();
    }
    var details = urls[current_index];
    tagged_log("Next option chosen: " + JSON.stringify(details));

    if (details.type == 'iframe' || details.type == 'image') {
        update_iframe_and_set_timeout(details, details);
    }
    else if (details.type == 'remote') {
        $.ajax({
            dataType: "json",
            url: details.url,
            data: "",
            error: function(jqXHR, textStatus, errorThrown) {
                tagged_log("Error in fetching remote object: " +
                            textStatus + " / " + errorThrown);

                // TODO - I don't think this is the right behavior, but I'm
                // supposed to be doing research or something. *sigh*.
                if (urls.length == 1) {
                    outstanding_change_request = setTimeout(
                        interval_timer, DEFAULT_SWITCH_INTERVAL);
                }
                else {
                    // This will catch you into infinite loop hell
                    holding = false;
                    interval_timer();
                }
            },
            success: function(received_data) {
                tagged_log("Received remote data: " +
                            JSON.stringify(received_data));
                update_iframe_and_set_timeout(
                    received_data, details);
            }
        });
    }
    else {
        tagged_log("Unknown type. Skipping.");
        return interval_timer();
    }
}

function update_urls(on_complete) {

    function on_update_received(data, textStatus, jqXHR) {
        tagged_log("Received updated data...");
        urls = data.urls;
    }

    function on_fail(jqxhr, textStatus, error) {
        tagged_log("Failed:" + textStatus + " : " + error);
    }

    tagged_log("Initiating JSON fetch.");
    //params = get_params();  // TODO - move to get params.
    //tags = get_anchor_tags();
    //URL = JSON_SOURCE + "/" + tags;
    tags = "bobwall";

    $.getJSON(JSON_SOURCE, "", on_update_received).fail(on_fail);

    // TODO
    if (tags != '3c') {
        $("#bar").css("display", "none");
    }
}

function kiosk_start() {
    tagged_log("Starting kiosk");
    polyfill();
    UPDATE_INTERVAL_OBJ = setInterval(update_urls, UPDATE_INTERVAL);
    outstanding_change_request = setTimeout(
        interval_timer, INITIAL_WAIT);
    init_update_check();
    update_urls();
    setup_manual_controls();
}

