var DEFAULT_OPTIONS = {
    legend: {
        position: 'right',
        textStyle: {
            color: 'white',
        },
    },
    //curveType: 'function',
    lineWidth: 3,
    pointSize: 0,
    //theme: 'maximized',
    vAxis: {
        viewWindowMode: 'maximized',
        /*
        viewWindow: {
           max: 20,
           min: 0,
        },
        max: 20,*/
        baselineColor: 'white',
        textStyle: { color: 'white', },
        titleTextStyle: { color: 'white', },
    },
    backgroundColor: 'black',
    hAxis: {
        minorGridlines: {
            count: 6,
        },
        baselineColor: 'white',
        textStyle: { color: 'white', },
        titleTextStyle: { color: 'white', },
    }
};

var API_HOST = "https://chezbob.ucsd.edu"
var TRANSACTION_URL = API_HOST + "/api/stats/v0.1/sales/get_month_transactions";

function get_transactions() {
    var promise = new Promise(function(resolve, reject) {
        console.log("Getting transactions");
        url = TRANSACTION_URL;
        $.getJSON(url, null, resolve).fail(
            function() { reject(Error("JSON request failed")) });
    });
    return promise;
}

function max_over(key, data, invert) {
    var max = 0;
    for (var i = 0; i < data.length; ++i) {
        if (key in data[i]) {
            if (invert) {
                if (data[i][key] < max) {
                    max = data[i][key];
                }
            } else {
                if (data[i][key] > max) {
                    max = data[i][key];
                }
            }
        }
    }
    return max;
}

function median_over(key, data) {
    var sorted = data.slice(0);
    sorted.sort(function(a, b) {
        return b[key] - a[key];
    });

    var result;
    if (sorted.length % 2 === 0)
        return (sorted[sorted.length / 2][key] +
                sorted[sorted.length / 2 + 1][key]) / 2;
    return sorted[Math.trunc(sorted.length / 2)][key];
}

function avg_over(key, data) {
    var sum = 0;
    var cnt = 0;
    for (var i = 0; i < data.length; ++i) {
        if (key in data[i]) {
            sum += data[i][key];
            ++cnt;
        }
    }
    return sum/cnt;
}

function nzc_over(key, data) {
    var cnt = 0;
    for (var i = 0; i < data.length; ++i) {
        if (key in data[i] && data[i][key] !== 0) {
            ++cnt;
        }
    }
    return cnt;
}

function loadTable(table, rows) {
    table.children( 'tbody' ).html('');
    var body = '';
    for (var i = 0; i < rows.length; ++i) {
        body += "<tr>";
        for (var j = 0; j < rows[i].length; ++j) {
            body += "<td>" + rows[i][j] + "</td>\n";
        }
        body += "</tr>\n";
    }
    table.children('tbody:last-child').append(body);
}

function table_prepare_rows(vals, cols, formats) {
    var returned = [];
    for (var i = 0; i < vals.length; ++i) {
        var row = [];
        for (var j = 0; j < cols.length; ++j) {
            var value = vals[i][cols[j]];

            if (formats && formats[j])
                value = formats[j](value);
            row.push(value);
        }
        returned.push(row);
    }
    return returned;
}

function top_by(key, values, n, invert) {
    values = values.slice(0);
    values.sort(function(a, b) {
        if (invert !== undefined && invert)
            return a[key] - b[key];
        return b[key] - a[key];
    });
    return values.slice(0, n);
}


function groupByKey(key, values) {
    return values.reduce(function(previous, x) {
        if (!(x[key] in previous)) {
            previous[x[key]] = [];
        }
        previous[x[key]].push(x);
        return previous;
    }, {});
}

function trunc_date_to_day(date) {
    //var new_date = new Date(date.getTime());
    //new_date.setMinutes(date.getMinutes() + date.getTimezoneOffset());
    //new_date.setMinutes(0);
    //new_date.setSeconds(0);

    var new_date2 = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate(),
        0, 0, 0, 0);
    return new_date2;
}


function update_text_noarrow(obj, value, is_currency, is_percentage) {
    var clean_value = Math.abs(value).toFixed(2);

    var prefix = "";
    if (is_currency) {
        prefix = "$";
    }
    var suffix = "";
    if (is_percentage) {
        suffix = "%";
    }

    if (value < 0)
        prefix = "-" + prefix;
    obj.text(prefix + clean_value + suffix);
}

function update_text(obj, value, is_currency, is_percentage) {
    var clean_value = Math.abs(value).toFixed(2);

    var prefix = "";
    if (is_currency) {
        prefix = "$";
    }
    var suffix = "";
    if (is_percentage) {
        suffix = "%";
    }

    obj.text(prefix + clean_value + suffix);
    obj.removeClass("positive");
    obj.removeClass("negative");
    if (value > 0)
        obj.addClass("positive");
    if (value < 0)
        obj.addClass("negative");
}

function process_new_data(transactions) {
    var now = new Date();
    transactions = transactions.map(function(x) {
        x.time = new Date(x.xacttime_s);
        return x;
    }).filter(function(x) {
        var diff = now - new Date(x.xacttime_s);
        //return (diff/1000/60/60/24/7 < 1);
        return (diff < 1000*60*60*24*28);
    });

    update_product_stats(transactions);
    update_transaction_stats(transactions);
    update_revenue_stats(transactions);
    update_user_stats(transactions);
}

function trigger_update() {
    return get_transactions().then(process_new_data);
}

function hide_loading_overlay() {
    console.log("Hiding loading overlay");
    $("#loading_overlay").css("display", "none");
}

function on_load() {
    init_revenue_stats(google);
    init_transaction_stats(google);
    init_product_stats(google);
    init_user_stats(google);
    trigger_update().then(hide_loading_overlay);
    setInterval(trigger_update, 5*60*1000);
}
