
var watcher = {};

watcher._update_overlay = function() {
    var n_shown = watcher._problem_table.find("tr").length - 1;  // inc. header
    if (n_shown > 0) {
        watcher._overlay.addClass("hidden");
    }
    else {
        watcher._overlay.removeClass("hidden");
    }
};

watcher._extract_name = function(desc) {
    var posn = desc.search(" \\(");
    if (posn == -1)
        return desc;
    return desc.substring(0, posn);
};

watcher._reorganize_values = function(values) {
    var new_values = {};
    var value;
    for (var i = 0; i < values.length; ++i) {
        value = values[i];
        new_values[value.bulkid] = value;
    }
    return new_values;
};

watcher._add_row = function(table, value) {
    var id = "row_" + value.bulkid;
    var row = "<tr id='" + id + "'>";

    //row += "<td><button class='inc'>+</button>";
    //row += "<button class='dec'>-</button>";
    //row += "<button class='resolve'>R</button></td>";

    row += "<td><button class='dec'>-</button></td>";
    row += "<td><span class='n_scanned'></span></td>";
    row += "<td><button class='inc'>+</button></td>";
    //row += "<td>/</td>";
    row += "<td><span class='expected'></span></td>";
    row += "<td><button class='resolve'>R</button></td>";
    row += "<td><span class='product_id'></span></td>";
    row += "<td><span class='description'></span></td>";

    row += "</tr>";

    table.append(row);
    var row_entry = table.find("#" + id);
    watcher._update_row(row_entry, value);

    var inc_btn = row_entry.find(".inc");
    var dec_btn = row_entry.find(".dec");
    var res_btn = row_entry.find(".resolve");

    inc_btn.on('click', function() {
        console.log("Increment requested on", value.bulkid);
        watcher._session.call("chezbob.accept_order.modify",
                              [value.bulkid, 1, null]).then(
            function(data) {
                console.log("Called increment", data);
            });
    });

    dec_btn.on('click', function() {
        console.log("Decrement requested on", value.bulkid);
        watcher._session.call("chezbob.accept_order.modify",
                              [value.bulkid, -1, null]).then(
            function(data) {
                console.log("Called decrement", data);
            });
    });

    res_btn.on('click', function() {
        console.log("Resolve requested on", value.bulkid);
        watcher._session.call("chezbob.accept_order.resolve",
                              [value.bulkid, null]).then(
            function(data) {
                console.log("Called resolve", data);
            });
    });
};

watcher._update_row = function(row, value) {
    row.find(".n_scanned").text(value.n_scanned);
    row.find(".expected").text(value.expected);
    row.find(".product_id").text(value.product_id);
    row.find(".description").text(watcher._extract_name(value.description));

    if(value.remaining < 0) {
        row.addClass("error");
    }
    else {
        row.removeClass("error");
    }
};

watcher._update_single_entry = function(value) {
    var table = watcher._problem_table;

    var id = "#row_" + value.bulkid;
    var preexisting = table.find(id);
    if (preexisting.length !== 0) {
        // We already have a row. Update it or delete it.
        if (0 === value.remaining) {
            console.log("Deleting row");
            preexisting.remove();
        }
        else {
            console.log("Updating row");
            watcher._update_row(preexisting, value);
        }
    }
    else {
        // We need to add this.
        watcher._add_row(table, value);
    }

};

watcher._update_table = function(new_values) {
    if (new_values === null)
        return;

    for (var i = 0; i < new_values.length; ++i) {
        watcher._update_single_entry(new_values[i]);
    }
    watcher._update_overlay();
};

watcher._handle_new_scan = function(args) {
    var value = args[0];
    var entry = value.bulk_item;

    entry.n_scanned = value.n_scanned;
    entry.remaining = value.remaining;
    entry.expected = value.expected;

    console.log("Scan detected:", entry);
    watcher._update_single_entry(entry);
    watcher._update_overlay();
};

watcher._on_connected = function() {
    console.log("On connected");
    watcher._session.call("chezbob.accept_order.get_unresolved", []).then(
        function(data) {
            console.log("Initially unresolved:", data);
            watcher._update_table(data);
        },
        function(err) {
            console.log("Failed to call function.", err);
        });
};

watcher._connect_ws = function() {
    var heartbeat_timer;

    var connection = new autobahn.Connection({
       url: watcher._endpoint, realm: "chezbob"
    });

    connection.onopen = function (session, details) {
        console.log("Connected");

        watcher._session = session;

        heartbeat_timer = setInterval(function () {
           session.publish('chezbob.heartbeat', [watcher._id]);
        }, 1000);

        session.subscribe('chezbob.accept_order.scan_result',
                          watcher._handle_new_scan).then(
           function (sub) {
              console.log('Subscribed to scan updates');
           },
           function (err) {
              console.log('Failed to subscribe to scan updates', err);
           }
        );
        
        watcher._on_connected();
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

    return connection.open();
};


watcher.init = function(endpoint, id) {
    watcher._endpoint = endpoint;
    watcher._id = id;

    watcher._problem_table = $("#problems");
    watcher._overlay = $("#overlay");

    console.log("Connecting to websocket");
    watcher._connect_ws();

};
