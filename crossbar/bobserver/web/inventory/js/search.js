
var search = {};

search.print_item = function(item) {
    var msg = "<div>";
    for (var i in item) {
        //console.log(i, item[i]);
        msg += "<b>" + i + ":</b> " + item[i] + "<br />\n";
    }
    msg += "</div>";
    search.body.html(msg);
};

search.init = function() {
    search.body = $("#search_tab");
    search.uninventoried = $("#uninventoried");
};

search.item_error = function(msg) {
    search.body.html(msg);
};

search.item_accept = function(item) {
    search.print_item(item);
};

search.on_activate = function() {
    server_inventory.get_uninventoried()
        .then(function(elements) {
            for (var i = 0; i < elements.length; ++i) {
                search._add_row(search.uninventoried, elements[i]);
        }
    });
};

search._extract_name = function(desc) {
    var posn = desc.search(" \\(");
    if (posn != -1)
        return desc.substring(0, posn);
    return desc;
};

search._add_row = function(table, value) {
    tbody = table.find("tbody");
    var id = "row_" + value.bulkid;
    var row = "<tr id='" + id + "'>";
    row += "<td>" + search._extract_name(value.description) + "</td>";
    row += "<td><label class='switch'>";
    row += "    <input type='checkbox' id='disable_toggle'>";
    row += "    <div class='slider round'></div></label></td>";
    row += "</tr>";

    tbody.append(row);

    //var row_entry = table.find("#" + id);
    /*
    var inc_btn = row_entry.find(".inc");
    inc_btn.on('click', function() {
        console.log("Increment requested on", value.bulkid);
        watcher._session.call("chezbob.accept_order.modify",
                              [value.bulkid, 1, null]).then(
            function(data) {
                console.log("Called increment", data);
            });
    });
    */
};
