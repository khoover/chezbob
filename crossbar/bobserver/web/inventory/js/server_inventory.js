var server_inventory = {};

// for the websocket heartbeat
server_inventory._NODE_NAME = (
    'inventory_' +
    Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1));

// What to do when we see an update
server_inventory._inventory_update_handler = function(args) {
    console.log("Inventory update handler triggered:", args);
    var item = args[0];
    server_inventory._on_update_callback(item[0], item[1]);
};

server_inventory._get_ws_url = function() {
    // If we're serving from a local file, assume the ws host is localhost.
    if (document.location.origin == "file://") {
        return "ws://127.0.0.1:8090/ws";
    } else {
        return (
            (document.location.protocol === "http:" ? "ws:" : "wss:") +
            "//" + document.location.host + "/ws");
    }
};

server_inventory._init_websockets = function() {
    var heartbeat_timer;

    var connection = new autobahn.Connection({
       url: server_inventory._get_ws_url(), realm: "chezbob"
    });

    connection.onopen = function (session, details) {
        console.log("Connected");

        server_inventory._session = session;

        session.subscribe(
            'chezbob.inventory.reset',
            function() {
                console.log("Received reset.");
                location.reload();
            });

        session.subscribe('chezbob.inventory.set_zeros',
                          server_inventory._on_zeros_callback);

        session.subscribe('chezbob.inventory.update',
                          server_inventory._inventory_update_handler).then(
           function (sub) {
              console.log('Subscribed to inventory updates');
           },
           function (err) {
              console.log('Failed to subscribe to inventory updates', err);
           }
        );

        heartbeat_timer = setInterval(function () {
           session.publish('chezbob.heartbeat', [server_inventory._NODE_NAME]);
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

server_inventory.add_to_inventory = function(bulkid, amount) {
    console.log("Calling add_to_inventory with " + bulkid + " and " + amount);
    return server_inventory._session.call(
        'chezbob.inventory.add_to_inventory', [bulkid, amount]);
};

server_inventory.zero_unprotected = function() {
    console.log("Calling zero_unprotected");
    return server_inventory._session.call(
        'chezbob.inventory.zero_unprotected', []);
};

server_inventory.reset = function(announce) {
    console.log("Calling reset");
    return server_inventory._session.call(
        'chezbob.inventory.reset', [announce]);
};

server_inventory.flag_for_no_update = function(bulkid) {
    console.log("Calling flag_for_no_update with " + bulkid);
    return server_inventory._session.call(
        'chezbob.inventory.flag_for_no_update', [bulkid]);
};

server_inventory.unflag_for_no_update = function(bulkid) {
    console.log("Calling unflag_for_no_update with " + bulkid);
    return server_inventory._session.call(
        'chezbob.inventory.unflag_for_no_update', [bulkid]);
};

server_inventory.get_inventory_value = function(bulkid) {
    console.log("Calling get_inventory_value with " + bulkid);
    return server_inventory._session.call(
        'chezbob.inventory.get_inventory_value', [bulkid]);
};

server_inventory.get_barcode_details = function(barcode) {
    console.log("Calling get_barcode_details with " + barcode);
    return server_inventory._session.call(
        'chezbob.inventory.get_barcode_details', [barcode]);
};

server_inventory.get_uninventoried = function() {
    console.log("Calling get_uninventoried");
    return server_inventory._session.call(
        'chezbob.inventory.get_uninventoried');
};

server_inventory.remove_from_inventory = function(bulkid) {
    console.log("Calling remove_from_inventory on " + bulkid);
    return server_inventory._session.call(
        'chezbob.inventory.remove_from_inventory', [bulkid]);
};

server_inventory.init = function(on_update_callback, on_zeros_callback) {
    server_inventory._init_websockets();
    server_inventory._on_update_callback = on_update_callback;
    server_inventory._on_zeros_callback = on_zeros_callback;
};

