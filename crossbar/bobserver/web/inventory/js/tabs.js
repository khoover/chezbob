
var tabs = {_current: null, _tabs: {}};

tabs.get_active = function() {
    return tabs._current.name;
};

tabs.activate = function(name) {
    console.log("Activating tab " + name +
                " (" + tabs._tabs[name].name + ")");

    // Disable current
    if (tabs._current !== undefined) {
        if (tabs._current.on_deactivate !== undefined) {
            tabs._current.on_deactivate();
        }
        tabs._current.div.removeClass("visible");
        tabs._current.btn.removeClass("active");
    }
    // Update current
    tabs._current = tabs._tabs[name];

    // Display new current
    tabs._current.div.addClass("visible");
    tabs._current.btn.addClass("active");

    if (tabs._current.on_activate !== undefined) {
        tabs._current.on_activate();
    }
};

tabs.register = function(name, btn_id, div_id, active, on_activate, on_deactivate) {
    var btn = $(document.getElementById(btn_id));
    var div = $(document.getElementById(div_id));

    var tab = {
        btn: btn, div: div, name: name,
        on_activate: on_activate, on_deactivate: on_deactivate,
    };

    if (active) {
        div.addClass("visible");
        btn.addClass("active");
        tabs._current = tab;
    }
    else {
    }

    tabs._tabs[name] = tab;
    btn.on("click", function() {
        tabs.activate(name);
    });
};
