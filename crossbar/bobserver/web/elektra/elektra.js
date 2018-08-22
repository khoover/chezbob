var NODE_NAME = 'elektra';

// All of this API started out as temporary.
// Hopefully it'll move to the WAMP endpoint at some point.
var BOB_HOST = "https://chezbob.ucsd.edu";
var LOGIN_URL = BOB_HOST + "/api/userauth/authenticate_from_bc/";
var EXTEND_URL = BOB_HOST + "/api/userauth/renew_token";
var BUY_URL = BOB_HOST + "/api/buy/by_barcode";

var AUTOLOGOUT_TIME_S = 60;

var WS_URL = ((document.location.protocol === "http:" ? "ws:" : "wss:") + "//" +
              document.location.host + "/ws");

var ACTUATE_FN_NAME = "chezbob.espresso.grinder.actuate_for";

var grinder_buttons = null;
var current_button = null;  // Current button that's vending
var current_user = null;  // Current user logged in.
var overlay = null;
var username_text = null;
var balance_text = null;
var remaining_text = null;

var connection = new autobahn.Connection({
    url: WS_URL,
    realm: "chezbob"
});

var heartbeat;

function on_barcode(args) {
    var barcode = args[0];
    console.log("Barcode:", barcode);

    if (current_user === null)
        try_login(barcode);
    else
        try_purchase(barcode);
}

function logout() {
    console.log("Logging out.");
    current_user = null;

    overlay.removeClass("hidden");
    username_text.text("");
    balance_text.text("");

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

function _update_balance(new_balance) {
    var bal_text;
    if (new_balance < 0)
        bal_text = '-$' + (-1 * new_balance).toFixed(2);
    else
        bal_text = '$' + new_balance.toFixed(2);
    balance_text.text(bal_text);
}

function try_purchase(barcode, cb, fail) {
    if (current_user === null)
        return;

    function purchased(info) {
        console.log("Received:", info);

        if (info.result == "success") {
            console.log("Purchase succeeded.");
            _update_balance(info.transaction.balance);
            show_snackbar_msg(info.transaction.xacttype);
            if (cb)
                cb(info);
        }
        else if (info.result == "error" &&
                 info.error == "Invalid barcode") {
            console.log("Invalid product barcode. Trying login.");
            try_login(barcode, null, fail);
        }
    }

    $.ajax({
        method: "POST",
        dataType: "json",
        url: BUY_URL,
        data: {token: current_user.token, barcode: barcode},
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
    _update_balance(current_user.balance);

    logout_timer = logoutTimer(AUTOLOGOUT_TIME_S);

    console.log("Remaining:", get_remaining());
}

function try_login(barcode, success, fail) {
    var url = LOGIN_URL + barcode;
    var res = $.getJSON(url, null, switch_user);
    if (success)
        res.then(success);
    if (fail)
        res.fail(fail);
}

function on_button_click() {
    if (current_button !== null)
        return;

    var me = $(this);
    grinder_buttons.prop('disabled', true);
    me.text("Purchasing!");

    var barcode = me.attr("barcode");
    var duration = parseFloat(me.attr("duration"));

    connection._session.call(ACTUATE_FN_NAME, [duration]).then(function() {
        current_button = me;
        try_purchase(barcode);
    }, function(error) {
        console.log(error);
        show_snackbar_msg("ERROR: Can't talk to grinder!");
        grinder_buttons.prop('disabled', false);
    });
}

function on_grinder_remaining(_, arg) {
    console.log("Countdown", arg.remaining);
    if (current_button === null)
        return;

    current_button.text("" + arg.remaining + "s remaining");
}

function on_grinder_deactivate() {
    console.log("Deactivate");
    if (current_button === null)
        return;

    current_button.text(current_button.attr("original_text"));
    grinder_buttons.prop('disabled', false);
    current_button = null;
}

function on_transaction(args) {
    var transaction = args[0];
    console.log("Transaction:", transaction);
}

connection.onopen = function (session, details) {
    console.log("Connected");

    session.subscribe('chezbob.scanner.elektra.barcode',
                      on_barcode).then(
       function (sub) {
          console.log('Subscribed to barcodes');
       },
       function (err) {
          console.log('Failed to subscribe to barcodes', err);
       }
    );

    session.subscribe('chezbob.espresso.grinder.deactivated',
                      on_grinder_deactivate).then(
       function (sub) {
          console.log('Subscribed to deactivate');
       },
       function (err) {
          console.log('Failed to subscribe to deactivate', err);
       }
    );

    session.subscribe('chezbob.espresso.grinder.remaining',
                      on_grinder_remaining).then(
       function (sub) {
          console.log('Subscribed to countdowns');
       },
       function (err) {
          console.log('Failed to subscribe to countdowns', err);
       }
    );

    heartbeat = setInterval(function () {
       session.publish('chezbob.heartbeat', [NODE_NAME]);
    }, 1000);
};

connection.onclose = function (reason, details) {
    console.log("Connection lost: " + reason);
    if (heartbeat) {
        clearInterval(heartbeat);
        heartbeat = null;
    }
};

// We open the connection as soon as we can.
connection.open();

$(function() {
    overlay = $("#overlay");
    username_text = $("#username");
    balance_text = $("#balance");
    remaining_text = $("#time_remaining");
    grinder_buttons = $(".grinder_btn");
    grinder_buttons.each(function() {
        var nt = $(this);
        nt.on('click', on_button_click);
        nt.attr("original_text", nt.text());
    });
});

function show_snackbar_msg(msg) {
    var x = document.getElementById("snackbar");

    // Add the "show" class to DIV
    x.className = "show";

    x.innerHTML = msg;

    function clear() {
        x.className = x.className.replace("show", "");
        x.innerHTML = '';
    }

    // After 3 seconds, remove the show class from DIV
    setTimeout(clear, 3000);
}

