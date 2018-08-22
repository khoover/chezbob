
var remote_scanner = {};

remote_scanner._play_sound = function(descriptor) {
    switch(descriptor) {
        case "success":
            sounds.happy_beep();
            break;
        case "warning":
            sounds.unhappy_beep();
            break;
        case "error":
            sounds.error_beep();
            break;
        //case "info":
        default:
            break;
    }
};

remote_scanner.on_data = function(data) {
    function response_received(resp) {
        console.log("Received:", resp);
        remote_scanner._play_sound(resp.result);
        remote_scanner._container.removeClass(remote_scanner._old_result);
        remote_scanner._container.addClass(resp.result);
        remote_scanner._header.html(resp.header);
        remote_scanner._details.html(resp.details);
        // So much trust I'm putting in these return values...
    }

    console.log("Caught barcode:", data);

    return remote_scanner._session
        .call(remote_scanner._fn_name, [data, remote_scanner._id, null])
        .then(response_received);
};

remote_scanner._connect_ws = function() {
    var heartbeat_timer;

    var connection = new autobahn.Connection({
       url: remote_scanner._endpoint, realm: "chezbob"
    });

    connection.onopen = function (session, details) {
        console.log("Connected");

        remote_scanner._session = session;

        heartbeat_timer = setInterval(function () {
           session.publish('chezbob.heartbeat', [remote_scanner._id]);
        }, 1000);
    };

    connection.onclose = function (reason, details) {
        console.log("Connection lost: " + reason);
        if (heartbeat_timer) {
           clearInterval(heartbeat_timer);
           heartbeat_timer = null;
        }

        // Fall back on polling if we couldn't get them.
        if (reason == "unreachable")
            console.log("Couldn't access WS endpoint.");
        else if (reason == "lost")
            console.log("WS connection lost-- auto reconnecting.");
    };

    connection.open();
};

remote_scanner.init = function(fn_name, endpoint, my_id) {
    remote_scanner._fn_name = fn_name;
    remote_scanner._endpoint = endpoint;
    remote_scanner._id = my_id;

    console.log("Remote scanner intializing to fn", fn_name, "at", endpoint);

    remote_scanner._header = $("#header");
    remote_scanner._details = $("#details");
    remote_scanner._container = $("#container");

    // Bit of a hack to remove all possibilities the first time.
    remote_scanner._old_result = "warning success error info";

    remote_scanner._connect_ws();
};
