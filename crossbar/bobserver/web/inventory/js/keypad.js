var keypad = {};

keypad.current_pending_total = 0;
keypad.current_server_total = 0;

keypad.register = function(id, func) {
    $(document.getElementById(id)).on('click', func);
};

keypad.get_basic_update = function(modifier) {
    return function(el) {
        keypad.current_pending_total = modifier(keypad.current_pending_total);
        console.log("Current pending total:", keypad.current_pending_total);
        keypad.update_display(true);
    };
};

keypad.register_count_update = function(id, func) {
    keypad.register(id, function() {
        if (keypad.item === undefined || keypad.item === null) {
            console.log("Skipping for undefined item.");
            return;
        }
        if (keypad.current_server_total == -1) {
            console.log("Skipping for disabled item.");
            return;
        }

        console.log(func);
        var resp = keypad.get_basic_update(func);
        return resp();
    });
};

keypad.register_static_button = function(id, step) {
    keypad.register_count_update(id, x => (x * 10 + step));
};

keypad.register_product_button = function(id, direction) {
    keypad.register_count_update(id, x => (x + direction));
};

keypad.register_bulk_button = function(id, direction) {
    keypad.register_count_update(
        id,
        x => (x + direction * keypad.item.quantity));
};

keypad.register_bs = function(id) {
    keypad.register_count_update(id, x => (x - (x % 10)) / 10);
};

keypad.register_confirm = function(id) {
    keypad.register(id, function() {
        if (keypad.item === undefined || keypad.item === null) {
            console.log("Skipping for undefined item.");
            return;
        }
        if (keypad.current_server_total == -1) {
            console.log("Skipping for disabled item.");
            return;
        }

        console.log(
            "Keypad confirm pressed with " +
            keypad.item.bulkid + " and " +
            keypad.current_pending_total);

        keypad.inventory_manager
            .add_to_inventory(keypad.item.bulkid, keypad.current_pending_total)
            .then(function() {
                keypad.current_pending_total = 0;
                keypad.update_display(true);
            });
    });
};

keypad.update_server_value = function(new_val) {
    console.log("Keypad updating server value with " + new_val);
    keypad.current_server_total = new_val;
    keypad.update_display(false);
};

keypad.update_display = function(silent) {
    if (    keypad.item === undefined ||
            keypad.item === null ||
            keypad.current_server_total == -1) {
        console.log("Blanking display for unknown or uninventoried item.");
        keypad.temp_bi.text("-");
        keypad.temp_p.text("-");
        keypad.temp_t.text("-");
        keypad.set_bi.text("-");
        keypad.set_p.text("-");
        keypad.set_t.text("-");

        if (keypad.current_server_total == -1) {
            keypad.item_name.text("DISABLED: " + keypad.item.description);
            keypad.item_box.addClass("error");
        }
        return;
    }
    if (keypad.current_server_total === null) {
        keypad.set_bi.text("-");
        keypad.set_p.text("-");
        keypad.set_t.text("-");
    }
    else {
        keypad.set_bi.text(
            Math.trunc(keypad.current_server_total / keypad.item.quantity));
        keypad.set_p.text(keypad.current_server_total % keypad.item.quantity);
        keypad.set_t.text(keypad.current_server_total);
    }

    keypad.temp_bi.text(
        Math.trunc(keypad.current_pending_total / keypad.item.quantity));
    keypad.temp_p.text(keypad.current_pending_total % keypad.item.quantity);
    keypad.temp_t.text(keypad.current_pending_total);

};

keypad.disable_space_activate = function() {
    // Make sure spaces don't activate buttons by accident.
    $("#keypad button").on( "keydown", function(k) { return k.which !== 32; });
};

keypad.find_objs = function() {
    keypad.set_bi = $("#bi_qs");
    keypad.set_p = $("#p_qs");
    keypad.set_t = $("#to_qs");
    keypad.temp_bi = $("#bi_qt");
    keypad.temp_p = $("#p_qt");
    keypad.temp_t = $("#to_qt");
    keypad.item_name = $("#keypad_item_name");
    keypad.item_box = $("#abovepad");
};

keypad.init = function(inventory_manager) {
    keypad.disable_space_activate();
    keypad.find_objs();
    keypad.inventory_manager = inventory_manager;

    keypad.register_static_button("btn_0", 0);
    keypad.register_static_button("btn_1", 1);
    keypad.register_static_button("btn_2", 2);
    keypad.register_static_button("btn_3", 3);
    keypad.register_static_button("btn_4", 4);
    keypad.register_static_button("btn_5", 5);
    keypad.register_static_button("btn_6", 6);
    keypad.register_static_button("btn_7", 7);
    keypad.register_static_button("btn_8", 8);
    keypad.register_static_button("btn_9", 9);
    keypad.register_product_button("btn_pp", 1);
    keypad.register_product_button("btn_pm", -1);
    keypad.register_bulk_button("btn_bp", 1);
    keypad.register_bulk_button("btn_bm", -1);
    keypad.register_bs("btn_bs");
    keypad.register_confirm("btn_c");

};

keypad.set_active_item = function(item) {
    console.log("Keypad setting active item to:", item);
    keypad.item = item;
    keypad.current_pending_total = 0;

    if (item === null) {
        return;
    }

    keypad.inventory_manager.get_inventory_value(item.bulkid)
        .then(function(value) {
            console.log("Keypad retrieved server inventory of:", value);

            if (value == -1)
                sounds.unhappy_beep();
            else
                sounds.happy_beep();

            keypad.update_server_value(value);
        });
};

keypad.item_error = function(msg) {
    keypad.item_name.text(msg);
    keypad.item_box.addClass("error");
    keypad.set_active_item(null);
};

keypad.item_accept = function(item) {
    keypad.set_active_item(item);
    keypad.item_name.text(item.description);
    keypad.item_box.removeClass("error");
};
