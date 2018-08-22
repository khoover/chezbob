var transaction_chart;
var transaction_value_day;
var transaction_value_week;
var transaction_value_month;

var google;

function init_transaction_chart(chart_id) {

    var data = new google.visualization.DataTable();
    var n_rows = data.getNumberOfRows();
    if (n_rows !== 0) {
        console.log("Clearing old data");
        data.removeRows(0, n_rows);
    }

    data.addColumn('date', "Day");
    data.addColumn('number', "Daily Sales");
    data.addColumn('number', "Daily average in past 7 days");
    data.addColumn('number', "Daily average in past month");

    var options = $.extend(true, {}, DEFAULT_OPTIONS);

    options.title = null; //'Sales and Deposits by Hour';
    options.vAxis.title = null; //'USD';
    options.hAxis.title = null; //'Day';
    //options.hAxis.direction = -1;
    options.legend.position = "bottom";
    options.chartArea = { 
        left: '5%', top: '2%', width:'95%', height: '90%'};
    transaction_chart = new google.visualization.ChartWrapper(
        {
            chartType: "LineChart",
            options: options,
            dataTable: data,
            containerId: chart_id,
        }
    );
}

function update_transaction_stats(transactions) {
    var graph_data = transaction_chart.getDataTable();

    var n_rows = graph_data.getNumberOfRows();
    if (n_rows !== 0) {
        console.log("Clearing old data");
        graph_data.removeRows(0, n_rows);
    }

    var total = 0;
    var day = 0;
    var week = 0;
    var max = 0;
    var min = 0;

    var now = new Date();
    var ONE_DAY = 1000*60*60*24;
    var ONE_WEEK = ONE_DAY*7;

    var purchases = transactions.filter(function(x) {return x.xactvalue < 0;});

    var grouped_by_day = groupByKey('day', purchases.map(function(x) {
        x.day = trunc_date_to_day(x.time);
        return x;
    }));

    /*
    var grouped_by_day = purchases.reduce(function(previous, val) {

        var day_epoch = Math.trunc(
            (now - (new Date(val.xacttime_s))) / ONE_DAY);

        if (!(day_epoch in previous)) {
            previous[day_epoch] = [];
        }

        previous[day_epoch].push(val);
        return previous;
    }, {});
    */

    var n_days = Object.keys(grouped_by_day).length;

    var data_points = Object.keys(grouped_by_day).map(function(x) {
        var sum = grouped_by_day[x].reduce(
            function(previous, y) {return previous - y.xactvalue}, 0);

        return { 
            time: trunc_date_to_day(
                new Date(grouped_by_day[x][0].xacttime_s)), 
            value: sum, 
        };
    });

    var rows = data_points.map(
        function(x) {
            total += x.value;

            if (now - x.time < ONE_WEEK) {
                console.log('week', x.time, x.value);
                week += x.value;
            }

            if (now - x.time < ONE_DAY) {
                console.log('day', x.time, x.value);
                day += x.value;
            }

            return [
                x.time,
                x.value,
                null,
                null
            ];
        });

    var week_avg = (week / 7);
    var month_avg = (total / n_days);

    function date_min(a, b) {
        return new Date(Math.min(a, b));
    }
    function date_max(a, b) {
        return new Date(Math.max(a, b));
    }

    var min_time = data_points.map(
        function(x) { return x.time }).reduce(date_min, new Date());
    var max_time = data_points.map(
        function(x) { return x.time }).reduce(date_max, data_points[0].time);
    console.log(min_time, max_time, week_avg, month_avg);

    rows.push([min_time, null, week_avg, month_avg]);
    rows.push([max_time, null, week_avg, month_avg]);

    graph_data.addRows(rows);
    transaction_chart.setOption("vAxis.minValue", 0);
    transaction_chart.draw();

    update_text_noarrow(transaction_value_day, day, true);
    update_text(transaction_value_week, day/week_avg*100 - 100, false, true);
    update_text(transaction_value_month, day/month_avg*100 - 100, false, true);
}

function init_transaction_stats(google_local) {
    google = google_local;
    transaction_value_day = $("#sales_today");
    transaction_value_week = $("#sales_vs_week");
    transaction_value_month = $("#sales_vs_month");
    init_transaction_chart('sales_chart');
}

