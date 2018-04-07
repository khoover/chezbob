var google;

var API_HOST = "https://chezbob.ucsd.edu";
var PRODUCT_DETAIL_URL = API_HOST + "/api/stats/v0.1/details/scan_barcode/";

function get_product_details(product) {
    function append_details(details) {
        product.details = details;
        return product;
    }

    var promise = new Promise(function(resolve, reject) {
        url = PRODUCT_DETAIL_URL + product.barcode;
        $.getJSON(url, null, resolve).fail(
            function() { reject(Error("JSON request failed"));});
    }).then(append_details);
    return promise;
}

function get_all_product_details(products) {
    var promises = [];
    for (var i = 0; i < products.length; ++i) {
        promises.push(get_product_details(products[i]));
    }
    return Promise.all(promises);
}

function update_product_stats(transactions) {

    var total = 0;
    var day = 0;
    var week = 0;
    var max = 0;
    var min = 0;

    var now = new Date();
    var now_s = now.getTime() / 1000;
    var ONE_DAY_S = 60*60*24;
    var ONE_DAY_MS = 1000*ONE_DAY_S;
    var ONE_WEEK_S = ONE_DAY_S*7;
    var ONE_WEEK_MS = 1000*ONE_WEEK_S;

    var purchases = transactions.filter(function(x) {return x.xactvalue < 0;});
    var by_barcode = groupByKey('barcode', purchases);
    var by_day = groupByKey('day', purchases.map(function(x) {
        x.day = trunc_date_to_day(x.time);
        return x;
    }));

    function calc_day_stats(arr) {
        var result = {
            count: 0,
            revenue: 0,
            distinct_users: 0,
            distinct_products: 0,
        };

        var users = {};
        var products = {};

        for (var i = 0; i < arr.length; ++i) {
            var curr = arr[i];
            result.count += 1;
            result.revenue += curr.xactvalue;
            users[curr.userid] = true;
            products[curr.barcode] = true;
        }

        result.distinct_users = Object.keys(users).length;
        result.distinct_products = Object.keys(products).length;
        return result;
    }

    function calc_product_stats(arr) {
        var result = {
            day_r: 0, 
            day_c: 0, 
            week_r: 0, 
            week_c: 0, 
            total_r: 0, 
            total_c: 0, 
            day_u: 0,
            week_u: 0,
            total_u: 0,
        };

        var day_users = {};
        var week_users = {};
        var total_users = {};

        for (var i = 0; i < arr.length; ++i) {
            var curr = arr[i];
            var diff = now_s - curr.xacttime_e;

            if (diff < ONE_DAY_S) {
                result.day_r += curr.xactvalue;
                result.day_c += 1;
                day_users[curr.userid] = true;
            }
            if (diff < ONE_WEEK_S) {
                result.week_r += curr.xactvalue;
                result.week_c += 1;
                week_users[curr.userid] = true;
            }

            result.total_r += curr.xactvalue;
            result.total_c += 1;
            total_users[curr.userid] = true;
        }
        result.day_u = Object.keys(day_users).length;
        result.week_u = Object.keys(week_users).length;
        result.total_u = Object.keys(total_users).length;
        return result;
    }

    var k;
    var result;

    var product_stats = [];
    for (k in by_barcode) {
        result = calc_product_stats(by_barcode[k]);
        result.barcode = k;
        product_stats.push(result);
    }

    var day_stats = [];
    for (k in by_day) {
        result = calc_day_stats(by_day[k]);
        result.day = k;
        day_stats.push(result);
    }

    function make_if_num(f) {
        function f_wrap(x) {
            if (typeof(x) == "number")
                return f(x);
            return x;
        }
        return f_wrap;
    }
    function to_decimal(x) { return x.toFixed(2); }
    //function positive_decimal(x) { return Math.abs(x).toFixed(2); }
    function dollar_value(x) { return "$" + Math.abs(x).toFixed(2); }

    function display_stats(table, rows) {
        get_all_product_details(rows)
            .then(function(x) {
                x.map(function(x) {
                    x.name = x.details.name;
                    return x;
                });

                var prepared_rows = table_prepare_rows(
                    x,
                    [
                        "name", 
                        "day_r",
                        "week_r",
                        "total_r",
                        "day_c",
                        "week_c",
                        "total_c",
                        "day_u",
                        "week_u",
                        "total_u",
                    ],
                    [
                        null, 
                        dollar_value,
                        dollar_value,
                        dollar_value,
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                    ]
                );
                loadTable(table, prepared_rows);
            });
    }

    display_stats(product_table_revenue_today, top_by('day_r', product_stats, 5, true));
    display_stats(product_table_volume_today, top_by('day_c', product_stats, 5));
    //display_stats(product_table_users_today, top_by('day_u', product_stats, 5));

    function make_row_product(name, suffix, data, conversion_f, invert) {
        var prefixes = ["day_", "week_", "total_"];
        var funcs = [max_over, avg_over, median_over];
        var cols = [name];
        for (var func_i = 0; func_i < funcs.length; func_i++) {
            for (var prefix_i = 0; prefix_i < prefixes.length; prefix_i++) {
                var key = prefixes[prefix_i] + suffix;
                cols.push(
                    conversion_f(
                        funcs[func_i](key, data, invert)));
            }
        }
        return cols;
    }

    function make_row_day(name, key, data, conversion_f, invert) {
        function empty() {return "";}
        var funcs = [
            max_over, empty, empty,
            avg_over, empty, empty, 
            median_over, empty, empty];

        var cols = [name];
        for (var func_i = 0; func_i < funcs.length; func_i++) {
            cols.push(
                conversion_f(
                    funcs[func_i](key, data, invert)));
        }
        return cols;
    }


    function calculate_stats_rows(products, days) {
        return [
            // TODO
            make_row_product(
                "Spend Per Product", "r", products, dollar_value, true),
            make_row_product(
                "Number of Purchases Per Product", "c", products, to_decimal),
            make_row_product(
                "Number of Distinct Users Per Product", "u", products, to_decimal),

            //make_row_day(
            //    "Revenue Per Day", "revenue", days, dollar_value, true),
            make_row_day(
                "Total Number of Purchases", "count", days,
                make_if_num(to_decimal)),
            make_row_day(
                "Distinct Active Products", "distinct_products", days,
                make_if_num(to_decimal)),
            ["Recent Distinct Active Products",
             nzc_over("day_c", products),
             nzc_over("week_c", products),
             nzc_over("total_c", products)],
        ];
    }

    var rows = calculate_stats_rows(product_stats, day_stats);

    loadTable(product_table_general_stats, rows);

    return;

}

function init_product_stats(google_local) {
    google = google_local;
    product_table_revenue_today = $("#top_product_revenue_today");
    product_table_volume_today = $("#top_product_volume_today");
    product_table_users_today = $("#top_product_users_today");
    product_table_general_stats = $("#product_stats_table");
}

