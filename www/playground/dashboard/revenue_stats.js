var revenue_chart;
var revenue_value_day;
var revenue_value_week;
var revenue_value_month;

var google;

function init_revenue_chart(chart_id) {

    var data = new google.visualization.DataTable();
    var n_rows = data.getNumberOfRows();
    if (n_rows !== 0) {
        console.log("Clearing old data");
        data.removeRows(0, n_rows);
    }

    data.addColumn('date', "Day");
    data.addColumn('number', "(Deposits - Purchases) since a month ago");
    data.addColumn('number', "(Deposits - Purchases) since 24 hours ago");
    data.addColumn('number', "(Deposits - Purchases) since a week ago");

    var options = $.extend(true, {}, DEFAULT_OPTIONS);

    options.title = null; //'Sales and Deposits by Hour';
    options.vAxis.title = null; //'USD';
    options.hAxis.title = null; //'Day';
    //options.hAxis.direction = -1;
    options.legend.position = "bottom";
    options.chartArea = { 
        left: '5%', top: '2%', width:'95%', height: '90%'};
    revenue_chart = new google.visualization.ChartWrapper(
        {
            chartType: "LineChart",
            options: options,
            dataTable: data,
            containerId: chart_id,
        }
    );
}

function update_revenue_stats(transactions) {
    var graph_data = revenue_chart.getDataTable();

    var n_rows = graph_data.getNumberOfRows();
    if (n_rows !== 0) {
        console.log("Clearing old data");
        graph_data.removeRows(0, n_rows);
    }

    var running = 0;
    var day = 0;
    var week = 0;
    var max = 0;
    var min = 0;

    var now = new Date();
    var ONE_DAY = 1000*60*60*24;
    var ONE_WEEK = ONE_DAY*7;

    var rows = transactions.map(
        function(x) {
            running += x.xactvalue;
            if (running > max) max = running;
            if (running < min) min = running;

            var xacttime = new Date(x.xacttime_s);
            var day_val = null;
            var week_val = null;

            if (now - xacttime < ONE_DAY) {
                day += x.xactvalue;
                day_val = day;
            }
            if (now - xacttime < ONE_WEEK) {
                week += x.xactvalue;
                week_val = week;
            }

            return [
                xacttime,
                running,
                day_val,
                week_val,
            ];
        });

    max = Math.max(Math.abs(min), max);
    min = -1 * max;

    graph_data.addRows(rows);
    revenue_chart.setOption("vAxis.maxValue", max);
    revenue_chart.setOption("vAxis.minValue", min);
    revenue_chart.draw();

    update_text(revenue_value_day, day, true);
    update_text(revenue_value_week, week, true);
    update_text(revenue_value_month, running, true);
}

function init_revenue_stats(google_local) {
    google = google_local;
    revenue_value_day = $("#revenue_value_day");
    revenue_value_week = $("#revenue_value_week");
    revenue_value_month = $("#revenue_value_month");
    init_revenue_chart('revenue_chart');
}

