var BOB_HOST = "https://chezbob.ucsd.edu";
var LOGIN_URL = BOB_HOST + "/api/userauth/authenticate_from_bc/";
var EXTEND_URL = BOB_HOST + "/api/userauth/renew_token";
var BUY_URL = BOB_HOST + "/api/buy/by_barcode";

var AUTOLOGOUT_TIME_S = 60;

var current_user = null;  // Current user logged in.
var overlay = null;
var username_text = null;
var balance_text = null;
var remaining_text = null;
var purchase_table = null;

// the URL of the WAMP Router (Crossbar.io)
//
var wsuri;
if (document.location.origin == "file://") {
    wsuri = "ws://127.0.0.1:8090/ws";

} else {
  wsuri = (
    (document.location.protocol === "http:" ? "ws:" : "wss:") +
    "//" + document.location.host + "/ws");
}

// the WAMP connection to the Router
//
var connection = new autobahn.Connection({
   url: wsuri,
   realm: "chezbob"
});

function clear_table(table) {
    table.find("tr").remove();
}

function add_row(table, value) {
    var id = "row_" + value.id;
    var row = "<tr id='" + id + "'>";
    row += "<td>" + value.transaction.xacttype + "</td>";
    row += "<td>$" + (-1 * value.transaction.xactvalue) + "</td>";
    row += "</tr>";
    table.append(row);
}

function on_barcode(barcode) {
    console.log("Barcode:", barcode);

    function on_purchase(details) {
        add_row(purchase_table, details);
        balance_text.text(details.transaction.balance);
    }

    if (current_user === null)
        try_login(barcode);
    else
        try_purchase(barcode, on_purchase);
}

function logout() {
    console.log("Logging out.");
    current_user = null;

    overlay.removeClass("hidden");
    username_text.text("");
    balance_text.text("");

    clear_table(purchase_table);

    if (logout_timer) {
        clearTimeout(logout_timer);
    }
}

function get_remaining() {
    var now = new Date();
    var etime = now.getTime() / 1000;
    return current_user.exp - etime;
}

function extend_login() {
    if (current_user === null)
        return;

    console.log("Extending time.", current_user);

    function extended(info) {
        console.log("Received:", info);
        current_user.token = info.token;
        current_user.exp = info.exp;
        if (logout_timer)
            clearTimeout(logout_timer);
        logout_timer = logoutTimer(AUTOLOGOUT_TIME_S);

        console.log("Remaining:", get_remaining());
    }

    $.ajax({
        method: "POST",
        dataType: "json",
        url: EXTEND_URL,
        data: {token: current_user.token},
        success: extended
    }).fail(function() { reject("renewal request failed"); });
}

function try_purchase(barcode, cb) {
    if (current_user === null)
        return;

    function purchased(info) {
        console.log("Received:", info);

        if (info.result == "success") {
            console.log("Purchase succeeded.");
            sounds.happy_beep();
            if (cb)
                cb(info);
        }
        else if (info.result == "error" &&
                 info.error == "Invalid barcode") {
            console.log("Invalid product barcode. Trying login.");
            try_login(barcode);
        }
    }

    $.ajax({
        method: "POST",
        dataType: "json",
        url: BUY_URL,
        data: {token: current_user.token, barcode: barcode, source: 'mobile'},
        success: purchased
    }).fail(function() { reject("purchase request failed"); });
}

function logoutTimer(t) {
    function lessOne() {
        t--;
        remaining_text.text(t);
        if (t === 0) {
            logout();
        }
    }
    remaining_text.text(t);
    return setInterval(lessOne, 1000);
}

function switch_user(new_user) {
    console.log("new_user:", new_user);
    if (new_user === null) {
        //todo - show modal or something
        console.log("Invalid barcode for logging in.");
        return;
    }

    current_user = new_user;

    overlay.addClass("hidden");
    username_text.text(current_user.username);
    balance_text.text(current_user.balance);

    logout_timer = logoutTimer(AUTOLOGOUT_TIME_S);

    console.log("Remaining:", get_remaining());
    sounds.happy_beep();
}

function try_login(barcode) {
    var url = LOGIN_URL + barcode;
    $.getJSON(url, null, switch_user)
        .fail(function() { reject("login request failed"); });
}

// fired when connection is established and session attached
//
connection.onopen = function (session, details) {
    console.log("Connected");
};


// fired when connection was lost (or could not be established)
//
connection.onclose = function (reason, details) {
   console.log("Connection lost: " + reason);
};

// now actually open the connection
//
connection.open();

$(function() {
    overlay = $("#overlay");
    username_text = $("#username");
    balance_text = $("#balance");
    remaining_text = $("#time_remaining");
    purchase_table = $("#purchase_table");
    barcode_catcher.init(on_barcode);
    sounds.init(on_barcode);
});
