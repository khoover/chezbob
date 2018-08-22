var cur_item;

function show_snackbar(msg) {
    // Get the snackbar DIV
    var x = document.getElementById("snackbar");

    // Set content.
    x.innerHTML = msg;

    // Add the "show" class to DIV
    x.className = "show";

    // After 3 seconds, remove the show class from DIV
    setTimeout(
        function(){ x.className = x.className.replace("show", ""); },
        3000
    );
}

function get_bulkitem_from_item(item) {
    switch (item.type) {
        case 'product':
            if (item.bulkitem === undefined || item.bulkitem === null)
                return "Undefined bulk item";
            return item.bulkitem;
        case 'bulkitem':
            return item;
        case 'unknown':
            return "Unknown item";
        default:
            console.log("Encountered unexpected item.type:", item.type);
            return "Unexpected item type";
    }
}

function barcode_callback(bc) {

    console.log("detected barcode:", bc);

    function update_item_failed(msg) {
        console.log("Failed:", msg);
        msg = "Error: " + msg;
        cur_item = null;

        var current_tab = tabs.get_active();

        switch(current_tab) {
            case "keypad":
                // This is always updated.
                break;
            case "search":
                // This is always updated.
                break;
            case "incremental":
                incremental_inventory.item_error(msg, "incremental");
                break;
            case "disable":
                incremental_inventory.item_error(msg, "disable");
                break;
            case "settings":
                // We don't want scanning in settings
                return;
            default:
                console.log("Unknown tab:", current_tab);
        }

        keypad.item_error(msg);
        search.item_error(msg);
        sounds.unhappy_beep();
    }

    function update_item_succeeded(item) {
        var bulkitem = get_bulkitem_from_item(item);
        if (typeof(bulkitem) === "string")
            return update_item_failed(bulkitem);

        console.log("Retrieved item info:", item);

        var current_tab = tabs.get_active();

        switch(current_tab) {
            case "keypad":
                // This is always updated.
                break;
            case "search":
                // This is always updated.
                break;
            case "incremental":
                incremental_inventory.item_accept(bulkitem, "incremental");
                break;
            case "disable":
                incremental_inventory.item_accept(bulkitem, "disable");
                break;
            case "settings":
                // We don't want scanning in settings
                sounds.unhappy_beep();
                return;
            default:
                console.log("Unknown tab:", current_tab);
        }

        cur_item = bulkitem;

        keypad.item_accept(bulkitem);
        search.item_accept(bulkitem);
    }

    barcode_cache.lookup(bc, update_item_succeeded, update_item_failed);
}

function on_inventory_update_callback(bulkid, amount) {
    console.log("Received inventory update callback");

    // Drop irrelvant ones on the floor
    if (bulkid != cur_item.bulkid)
        return;

    keypad.update_server_value(amount);
    incremental_inventory.update_server_value(amount);
}

function on_zero_callback() {
    console.log("Zeros set!");
    show_snackbar("Zeros set!");
}

function init() {
    document.onkeypress = console.log;

    tabs.register("incremental", "incr_tab_btn", "incremental_tab");
    tabs.register("disable", "disa_tab_btn", "disable_tab");
    tabs.register("keypad", "kypd_tab_btn", "keypad_tab", true);
    tabs.register("search", "srch_tab_btn", "search_tab", false, search.on_activate);
    tabs.register("settings", "gear_tab_btn", "settings_tab");

    sounds.init();
    search.init();
    barcode_cache.init(server_inventory.get_barcode_details);
    incremental_inventory.init();

    keypad.init(server_inventory);
    barcode_catcher.init(barcode_callback);
    server_inventory.init(on_inventory_update_callback, on_zero_callback);
    incremental_inventory.init(on_inventory_update_callback);

    var zeros_btn = $("#zeros_btn");
    var zeros_button_pending = null;
    zeros_btn.on('click', function() {
        if (!confirm("Are you sure you want to set all uninventoried/unprotected items to have zero inventory?"))
            return;

        zeros_btn.addClass("pending");
        zeros_btn.removeClass("success error");
        zeros_btn.text("...submitting...");

        function reset() {
            zeros_btn.removeClass("success error pending");
            zeros_btn.text("Commit");
        }

        server_inventory.zero_unprotected().then(
            function() {
                //success
                if (zeros_button_pending !== null) {
                    clearTimeout(zeros_button_pending);
                }
                zeros_btn.removeClass("error pending");
                zeros_btn.addClass("success");
                zeros_btn.text("Success!");
                zeros_button_pending = setTimeout(reset, 5000);
            },
            function(err) {
                //failure
                if (zeros_button_pending !== null) {
                    clearTimeout(zeros_button_pending);
                }
                console.log(err);
                zeros_btn.removeClass("success pending");
                zeros_btn.addClass("error");
                zeros_btn.text("Error!");
                zeros_button_pending = setTimeout(reset, 15000);
            }
        );
    });

    var reset_button_pending = null;
    var reset_btn = $("#reset_btn");
    reset_btn.on('click', function() {

        if (!confirm("Are you sure you want to reset?"))
            return;

        reset_btn.addClass("pending");
        reset_btn.removeClass("success error");
        reset_btn.text("...submitting...");

        function reset() {
            reset_btn.removeClass("success error pending");
            reset_btn.text("Reset");
        }

        server_inventory.reset(true).then(
            function() {
                //success
                if (reset_button_pending !== null)
                    clearTimeout(reset_button_pending);
                reset_btn.removeClass("error pending");
                reset_btn.addClass("success");
                reset_btn.text("Reset!");
                reset_button_pending = setTimeout(reset, 5000);
            },
            function(err) {
                //failure
                console.log(err);
                if (reset_button_pending !== null)
                    clearTimeout(reset_button_pending);
                reset_btn.removeClass("success pending");
                reset_btn.addClass("error");
                reset_btn.text("Error!");
                reset_button_pending = setTimeout(reset, 15000);
            }
        );
    });
}
