
function update_user_stats(transactions) {

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
    var by_user = groupByKey('userid', purchases);
    var by_product = groupByKey('barcode', purchases);
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


    function calc_user_stats(arr) {
        var result = {
            day_r: 0,
            day_c: 0,
            week_r: 0,
            week_c: 0,
            total_r: 0,
            total_c: 0,
            day_p: 0,
            week_p: 0,
            total_p: 0,
        };

        var day_products = {};
        var week_products = {};
        var total_products = {};

        for (var i = 0; i < arr.length; ++i) {
            var curr = arr[i];
            var diff = now_s - curr.xacttime_e;

            if (diff < ONE_DAY_S) {
                result.day_r += curr.xactvalue;
                result.day_c += 1;
                day_products[curr.barcode] = true;
            }
            if (diff < ONE_WEEK_S) {
                result.week_r += curr.xactvalue;
                result.week_c += 1;
                week_products[curr.barcode] = true;
            }

            result.total_r += curr.xactvalue;
            result.total_c += 1;
            total_products[curr.barcode] = true;
        }
        result.day_p = Object.keys(day_products).length;
        result.week_p = Object.keys(week_products).length;
        result.total_p = Object.keys(total_products).length;
        return result;
    }

    var k;
    var result;

    var user_stats = [];
    for (k in by_user) {
        result = calc_user_stats(by_user[k]);
        result.userid = k;
        user_stats.push(result);
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

    function make_row_user(name, suffix, data, conversion_f, invert) {
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



    function calculate_rows(users, days) {
        return [
            make_row_user("Spend per User", "r", users, dollar_value, true),
            make_row_user("Number of Purchases Per User", "c", users, to_decimal),
            make_row_user("Numer of Distinct Products Per User", "p", users, to_decimal),
            make_row_day(
                "Distinct Active Users", "distinct_users", days,
                make_if_num(to_decimal)),
            ["Recent Active Users",
             nzc_over("day_c", users),
             nzc_over("week_c", users),
             nzc_over("total_c", users)],
        ];
    }

    var rows = calculate_rows(user_stats, day_stats);

    loadTable(user_table, rows);

    return;

}

function init_user_stats(google_local) {
    user_table = $("#user_stats_table");
}

