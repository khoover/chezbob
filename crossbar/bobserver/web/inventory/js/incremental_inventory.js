var PENDING_BARCODE_TEXT = "[waiting for barcode]";
var RESULT_DISPLAY_TIME_MS = 5000;

var incremental_inventory = {_pending_timeout: null};

incremental_inventory.init = function() {
    incremental_inventory.elements = {
        incremental: {
            label: $("#incremental_name"),
            body: $("#incremental_body"),
            toggle: $("#product_case_toggle"),
        },
        disable: {
            label: $("#disable_name"),
            body: $("#disable_body"),
            toggle: $("#disable_toggle"),
        },
    };
    incremental_inventory.srv_counts = {
        b: $("#inc_b"),
        l: $("#inc_l"),
        t: $("#inc_t"),
    };
};

incremental_inventory._add_item = function(bulkitem) {
    var els = incremental_inventory.elements.incremental;

    var offset = 1;
    if (els.toggle.prop("checked"))
        offset = bulkitem.quantity;

    console.log("Incrementing", bulkitem.bulkid, "by", offset);

    server_inventory.add_to_inventory(bulkitem.bulkid, offset).then(
        function() {
            incremental_inventory.item_accepted(bulkitem, "incremental");
        },
        function(err) {
            incremental_inventory.item_error(err);
        }
    );
};

incremental_inventory._toggle_disabled = function(bulkitem) {
    var els = incremental_inventory.elements.disable;

    if (els.toggle.prop("checked")) {
        console.log("Enabling", bulkitem.bulkid);
        server_inventory.unflag_for_no_update(bulkitem.bulkid).then(
            function() {
                incremental_inventory.item_accepted(bulkitem, "disable");
            },
            function(err) { incremental_inventory.item_error(err); }
        );
    }
    else {
        console.log("Disabling", bulkitem.bulkid);
        server_inventory.flag_for_no_update(bulkitem.bulkid).then(
            function() {
                incremental_inventory.item_accepted(bulkitem, "disable");
            },
            function(err) {
                incremental_inventory.item_error(err);
            }
        );
    }

};

incremental_inventory.item_accepted = function(bulkitem, type) {
    var els = incremental_inventory.elements[type];

    function reset() {
        els.body.removeClass("success error");
        els.body.addClass("pending");
        els.label.text(PENDING_BARCODE_TEXT);
        incremental_inventory._pending_timeout = null;
    }

    if (incremental_inventory._pending_timeout !== null) {
        clearTimeout(incremental_inventory._pending_timeout);
    }

    els.label.text(bulkitem.description);
    els.body.removeClass("error pending");

    incremental_inventory._pending_timeout = setTimeout(
        reset, RESULT_DISPLAY_TIME_MS);
};

incremental_inventory.item_accept = function(bulkitem, type) {
    var els = incremental_inventory.elements[type];
    console.log(incremental_inventory.elements, type);
    els.label.text("...pending...");
    els.body.removeClass("error");
    els.body.addClass("pending");

    incremental_inventory.item = bulkitem;

    switch(type) {
        case "incremental":
            incremental_inventory._add_item(bulkitem);
            break;
        case "disable":
            incremental_inventory._toggle_disabled(bulkitem);
            break;
        default:
            console.log("ERROR: Unknown type.");
    }
};

incremental_inventory.item_error = function(msg, type) {
    var els = incremental_inventory.elements[type];
    els.label.text(msg);
    els.body.removeClass("pending");
    els.body.addClass("error");
};

incremental_inventory.update_server_value = function(new_value) {
    var item = incremental_inventory.item;
    var srv_counts = incremental_inventory.srv_counts;
    srv_counts.b.text(Math.trunc(new_value / item.quantity));
    srv_counts.l.text(new_value % item.quantity);
    srv_counts.t.text(new_value);
};
