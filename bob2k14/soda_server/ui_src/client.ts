/// <reference path="../typings/tsd.d.ts"/>

import $ = require("jquery");
jQuery = $;
import Q = require("q");
import io = require("socket.io");
var rpc = require("rpc");
var bootstrap = require("bootstrap");
var d3 = require('d3-browserify');
var moment = require('moment');

export enum ClientType {
    Terminal = 0,
    Soda = 1
}

enum log_level
{
    FATAL = 60,
    ERROR = 50,
    WARN = 40,
    INFO = 30,
    DEBUG = 20,
    TRACE = 10
}

export class ClientLogger
{
    channel;

    trace = (msg) => { this.channel.log(log_level.TRACE, msg); }
    debug = (msg) => { this.channel.log(log_level.DEBUG, msg); }
    info = (msg) => { this.channel.log(log_level.INFO, msg); }
    warn = (msg) => { this.channel.log(log_level.WARN, msg); }
    error = (msg) => { this.channel.log(log_level.ERROR, msg); }
    fatal = (msg) => { this.channel.log(log_level.FATAL, msg); }

    constructor (channel)
    {
        this.channel = channel;
    }
}
export class Client
{
    server_channel;
    log;
    bcstats;
    timeout_timer;
    time: number;
    time_pause: boolean;
    transactionindex : number;
    currenttransactions;

    type : ClientType;
    id;
    current_user;

    startTimeout(client: Client)
    {
        if (client.timeout_timer != null)
        {
            clearInterval(client.timeout_timer);
        }

        client.time = 30;
        $("#timeout").text(client.time+"s");
        $("#timeoutpanel").removeClass('hidden');
        $("#moretimebtn").removeClass('hidden');
        client.timeout_timer = setInterval(function ()
                {
                    if (!client.time_pause)
                    {
                        client.time = client.time - 1;
                    }
                    if (client.time == 0)
                    {
                        client.server_channel.logout();
                    }
                    if (client.time < 5)
                    {
                        $("body").css('background-color', '#ffaaaa');
                    }
                    else
                    {
                        $("body").css('background-color', '#fff');
                    }
                    $("#timeout").text(client.time+"s");
                }, 1000);
    }

    stopTimeout(client:Client)
    {
        if (client.timeout_timer != null)
        {
            clearInterval(client.timeout_timer);
            client.timeout_timer = null;
        }

        $("#timeoutpanel").addClass('hidden');
        $("#moretimebtn").addClass('hidden');
        $("body").css('background-color', '#fff');
    }

    logout(client:Client)
    {
        client.stopTimeout(client);
        $("#logout").addClass('hidden');
        $("#login").removeClass('hidden');
        $("#loginpanel").addClass('hidden');
        $(".username").text("");
        $("#balancepanel").addClass('hidden');
        $("#carousel").removeClass('hidden');
        $("#mainui").addClass('hidden');
        $("#purchases-table tbody").empty();
        $("#transactionhistory-table tbody").empty();
        client.current_user = null;
        client.time_pause = false;
    }

    login(client: Client, logindata)
    {
        $("#login").addClass('hidden');
        $("#logout").removeClass('hidden');
        $("#loginpanel").removeClass('hidden');
        $(".username").text(logindata.username);
        $("#balancepanel").removeClass('hidden');
        client.setBalance(client,logindata.balance);
        $("#carousel").addClass('hidden');
        $("#mainui").removeClass('hidden');
        $("#purchases-table tbody").empty();
        client.startTimeout(client);
        client.setUIscreen(client, "mainpurchase");
        client.current_user = logindata;
        client.time_pause = false;

        if (logindata.roles.admin || logindata.roles.restocker)
        {
            $("#adminbtn").removeClass('hidden');
        }
        else
        {
            $("#adminbtn").addClass('hidden');
        }
    }

    setUIscreen(client: Client, screen: string)
    {
        $(".ui-screen").addClass('hidden');
        $("#" + screen).removeClass('hidden');
        client.log.trace("Switching to screen " + screen);
    }

    setBalance(client: Client, balance : string)
    {
        if (parseFloat(balance) < parseFloat("0.0"))
        {
            $("#balancepanel a").css('color', '#ff0000');
            $("#balancewarn").removeClass('hidden');
            $("#balancewarn").tooltip('show');
            setTimeout(function() {
                $("#balancewarn").tooltip('hide')
            }, 3000);
        }
        else
        {
            $("#balancepanel a").css('color', '#00ff00');
            $("#balancewarn").addClass('hidden');
            $("#balancewarn").tooltip('hide');
        }

        $('.balance').text(balance);
    }

    updateTransactions(client: Client)
    {
        client.server_channel.transactionhistory(client.transactionindex * 5, 5).then(
            function (transaction)
            {
                if (client.transactionindex == 0)
                {
                    $("#transactionhistory-newer").addClass("disabled");
                    $("#transactionhistory-older").removeClass("disabled");
                }
                else if (5 + (5 * client.transactionindex) > transaction.count)
                {
                    $("#transactionhistory-older").addClass("disabled");
                    $("#transactionhistory-newer").removeClass("disabled");
                }
                else
                {
                    $("#transactionhistory-older").removeClass("disabled");
                    $("#transactionhistory-newer").removeClass("disabled");
                }

                $("#transactionhistory-table tbody").empty();
                client.currenttransactions = transaction.rows;
                $.each(transaction.rows, function (idx, row)
                    {
                         $("#transactionhistory-table tbody").append(
                             "<tr><td>" + moment(row.xacttime).format("MM/D/YY hh:mm a") +
                             "</td><td>" + row.xacttype +
                             "</td><td>" + row.xactvalue +
                             "</td><td><a href='#' class='btn btn-info transactiondetail' data-id='" + idx +  "'>Detail</a>" +
                             "</td></tr>");
                    });

                $(".transactiondetail").on('click', function(e) {
                    var xact = client.currenttransactions[$(this).data('id')];
                    $("#transactiondetails-table tbody").empty();
                    $("#transactiondetails-table tbody").append('<tr><td>Id</td><td>' + xact.id + '<td></tr>');
                    $("#transactiondetails-table tbody").append('<tr><td>Time</td><td>' + xact.xacttime + '<td></tr>');
                    $("#transactiondetails-table tbody").append('<tr><td>Value</td><td>' + xact.xactvalue + '<td></tr>');
                    $("#transactiondetails-table tbody").append('<tr><td>Type</td><td>' + xact.xacttype + '<td></tr>');
                    $("#transactiondetails-table tbody").append('<tr><td>Source</td><td>' + xact.source + '<td></tr>');
                    $("#transactiondetails-table tbody").append('<tr><td>Barcode</td><td>' + xact.barcode + '<td></tr>');
                    $("#transactiondetails-table tbody").append('<tr><td>User ID</td><td>' + xact.userid + '<td></tr>');
                    client.setUIscreen(client, 'transactions-detail');
        });

            }
        );
    }

    updateBarcodes(client: Client)
    {
        client.server_channel.get_barcodes().then(
                    function (barcodes)
                    {
                        $("#barcodes-table tbody").empty();
                        $.each(barcodes, function (idx, barcode)
                            {
                                $("#barcodes-table tbody").append('<tr><td>' + barcode.barcode + '</td><td><a href="#" class="btn btn-danger deregisterbarcode" data-barcode="' + barcode.barcode + '">Forget</a></td></tr>');
                            });
                        $(".deregisterbarcode").on('click', function(e)
                            {
                                var barcode = $(this).data('barcode');
                                client.server_channel.forget_barcode(barcode);
                            })
                    }
                )
    }
    connect(client: Client)
    {
        rpc.connect(window.location.protocol + '//' + window.location.hostname + ':' + window.location.port);
        rpc.loadChannel('serverChannel').then(
                function (channel)
                {
                    client.server_channel = channel;
                    client.log = new ClientLogger(channel);
                    client.log.info("New client connected");
                    var barcodes = ['782740', '496340', '049000042566', '120130', '120500',
                                '783150', '783230', '120850', '496580'];
                    client.bcstats = {};
                    barcodes.forEach( function(barcode) {
                        channel.barcodestats(barcode).then(function (res)
                            {
                                client.bcstats[barcode] = res;
                                console.log(barcode + ": " + res);
                            });
                    });
                }
                );
        rpc.expose('clientChannel',
                {
                    gettype: function()
                    {
                        return {type: client.type, id: client.id };
                    },
                    login: function (logindata)
                    {
                        client.login(client, logindata);
                    },
                    logout: function()
                    {
                        client.logout(client);
                    },
                    addpurchase: function(purchasedata)
                    {
                        //purchases are usually negative, so don't display unless positive.
                        var purchaseprice = purchasedata.amount[0] === '-' ? purchasedata.amount.substring(1) : '+' + purchasedata.amount;
                        $("#purchases-table tbody").append("<tr><td>" + purchasedata.name + "</td><td>" + purchaseprice + "</td>");
                        client.setBalance(client, purchasedata.newbalance);
                        //maybe we don't want to call this on every purchase?
                        $("#sodadialog").modal('hide');
                        client.time_pause = false;
                        client.setUIscreen(client,"mainpurchase");
                    },
                    displayerror: function(icon, title, text)
                    {
                        $("#errortext").text(text);
                        $("#errortitle").text(title);
                        $("#erroricon").removeClass().addClass("fa-5x fa " + icon);
                        //if soda errors, we are no longer dispensing
                        $("#sodadialog").modal('hide');
                        $("#errordialog").modal('show');
                        client.time_pause = false;
                    },
                    displaysoda: function(requested_soda, soda_name)
                    {
                        //TODO: use requested_soda to display logo.
                        $("#sodatext").text("Dispensing " + soda_name);
                        $("#sodadialog").modal('show');
                        client.time_pause = true;
                    },
                    updatebarcodes: function()
                    {
                        client.updateBarcodes(client);
                    },
                    updateuser: function(user)
                    {
                        client.current_user = user;
                    },
                    updatevendstock: function(stock)
                    {
                        console.log(stock);
                    },
                    reload: function()
                    {
                        window.location.reload();
                    }
                }
                );
    }

    setup_ui(client: Client)
    {
        $("#loginform").submit(function(e) {
            client.log.debug("Begin login attempt...");
            e.preventDefault();
            client.server_channel.authenticate($("#username").val(), $("#password").val()).then(
                function (val)
                {
                    if (!val)
                    {
                        //Authentication failure...
                    }
                        $("#login").removeClass('open');
                        $('#loginform').trigger('reset');
                }
                ).catch(function(err)
                    {
                        client.log.error(err);
                        $("#login").removeClass('open');
                        $('#loginform').trigger('reset');
                    }
                )
        });

        $("#errordialog").modal({show:false});
        $("#errordialog").on('shown.bs.modal', function () {
            setTimeout(function()
                {
                    $("#errordialog").modal('hide');
                }, 3000);
        });
        $(".optbutton").on('click', function(e)
                {
                    client.setUIscreen(client, $(this).data('target'));
                });

        $(".tsidebutton").on('click', function(e)
                {
                    client.setUIscreen(client, $(this).data('target'));
                });

        $(".disabletimeout").on('click', function(e)
                {
                    client.stopTimeout(client);
                })
        $("#balancewarn").tooltip({
            title: "Your balance is negative. Please add funds to your account.",
            placement: 'bottom'
        });

        $("#logoutbtn").on('click', function() {
            client.server_channel.logout();
        });
        $("#moretimebtn").on('click', function() {
            client.time = client.time + 30;
            client.log.trace("User added 30 seconds to autologout");
        });

        $("#transactions-btn").on('click', function() {
            //inital pager state.
            $("#transactionhistory-newer").addClass("disabled");
            $("#transactionhistory-older").removeClass("disabled");

            //start with 10 most recent transactions
            client.transactionindex = 0;
            client.updateTransactions(client);
        });

        $("#transactionhistory-newerbtn").on('click', function() {
            if (client.transactionindex != 0)
            {
                client.transactionindex--;
                client.updateTransactions(client);
            }
        });

        $("#transactionhistory-olderbtn").on('click', function() {
            client.transactionindex++;
            client.updateTransactions(client);
        });

        $("#profile-btn").on('click', function() {
            $("#profile-username").val(client.current_user.username);
            $("#profile-email").val(client.current_user.email)
        });

        $("#profile-barcodebtn").on('click', function()
        {
            client.updateBarcodes(client);
            client.server_channel.learnmode_barcode(true);
        });

        $("#setbarcode-exitbtn").on('click', function()
        {
            client.server_channel.learnmode_barcode(false);
        });

        $("#profile-passwordbtn").on('click', function()
        {
            (<HTMLFormElement>$("#setpasswordform")[0]).reset();
            if (client.current_user.pwd)
            {
                $("#setpassword-current-div").removeClass('hidden');
                $("#setpassword-enable").prop("checked", true);
                $("#setpassword-new-div").removeClass('hidden');
                $("#setpassword-confirm-div").removeClass('hidden');
            }
            else
            {
                $("#setpassword-current-div").addClass('hidden');
                $("#setpassword-enable").prop("checked", false);
                $("#setpassword-new-div").addClass('hidden');
                $("#setpassword-confirm-div").addClass('hidden');
            }
        });

        $("#setpassword-confirm").on('input', function(e)
                {
                    if (this.value !== $("#setpassword-new").val())
                    {
                        this.setCustomValidity('The confirmation password must match.');
                    }
                    else
                    {
                        this.setCustomValidity('');
                    }
                });

        $("#setpasswordform").on('submit', function(e)
                {
                    client.log.info("Begin password change request.");
                    e.preventDefault();
                    client.server_channel.changepassword($("#setpassword-enable").prop('checked'),
                        $("#setpassword-new").val(), $("#setpassword-current").val());
                }
        );
        $("#setpassword-enable").on('change', function()
                {
                    if (this.checked)
                    {
                        $("#setpassword-new-div").removeClass('hidden');
                        $("#setpassword-confirm-div").removeClass('hidden');
                    }
                    else
                    {
                        $("#setpassword-new-div").addClass('hidden');
                        $("#setpassword-confirm-div").addClass('hidden');
                    }
                })

        $("#domanualpurchasebtn").on('click', function() {
            //do a manual purchase for this session
            //probably should prevent autologout
            if (!(<any>$("#domanualpurchasebtn").closest('form')[0]).checkValidity())
            {
                return;
            }
            var paddedcents = "0" + $("#manualpurchase-cents").val();
            paddedcents = paddedcents.slice(-2);
            var amt = $("#manualpurchase-dollars").val() + "." + paddedcents;
            $("#manualpurchase-cents").val("00");
            $("#manualpurchase-dollars").val("0");
            client.server_channel.manualpurchase(amt);
        })

        $("#domanualdepositbtn").on('click', function() {
            //do a manual purchase for this session
            //probably should prevent autologout
            if (!(<any>$("#domanualdepositbtn").closest('form')[0]).checkValidity())
            {
                return;
            }
            var paddedcents = "0" + $("#manualdeposit-cents").val();
            paddedcents = paddedcents.slice(-2);
            var amt = $("#manualdeposit-dollars").val() + "." + paddedcents;
            $("#manualdeposit-cents").val("00");
            $("#manualdeposit-dollars").val("0");
            client.server_channel.manualdeposit(amt);
        })

        $("#dotransferbtn").on('click', function() {
            //do a manual purchase for this session
            //probably should prevent autologout
            if (!(<any>$("#dotransferbtn").closest('form')[0]).checkValidity())
            {
                return;
            }
            var paddedcents = "0" + $("#transfer-cents").val();
            paddedcents = paddedcents.slice(-2);
            var amt = $("#transfer-dollars").val() + "." + paddedcents;
            $("#transfer-cents").val("00");
            $("#transfer-dollars").val("0");
            client.server_channel.transfer(amt, $("#transfer-user").val());
        })

        $("#message_bug-form").on('submit', function(e) {
            e.preventDefault();
            client.log.info("Sending a bug report.");
            client.server_channel.bug_report($("#message_bug-report").val()).then(function ()
                {
                    (<HTMLFormElement>$("#message_bug-form")[0]).reset();
                    client.setUIscreen(client, "message");
                });
        })

        $("#message_issues-form").on('submit', function(e) {
            e.preventDefault();
            client.log.info("Sending an account issue report.");
            client.server_channel.issue_report($("#message_issues-report").val()).then(function ()
                {
                    (<HTMLFormElement>$("#message_issues-form")[0]).reset();
                    client.setUIscreen(client, "message");
                });
        })

        $("#message_comments-form").on('submit', function(e) {
            e.preventDefault();
            client.log.info("Sending an account comment report.");
            client.server_channel.comment_report($("#message_comments-anonymous").prop('checked'), $("#message_comments-report").val()).then(function ()
                {
                    (<HTMLFormElement>$("#message_comments-form")[0]).reset();
                    client.setUIscreen(client, "message");
                });
        })

        $("#message_oos-search").on('keyup', function(e) {
            var searchinput = $("#message_oos-search").val();
            client.log.trace("OOS search input set to " + searchinput);
            $("#message_oos-list").empty();
            client.server_channel.oos_search(searchinput).then(
                function(results)
                {
                    results.forEach(function(result)
                        {
                            $("#message_oos-list").append("<a href='#' class='list-group-item oos_search_item' data-barcode='" + result.barcode + "'>" + result.name + "</a>")
                        });
                    $(".oos_search_item").on('click', function(e)
                        {
                            var item = $(this).data('barcode');
                            client.log.info("Sending OOS report for barcode " + item);
                            client.server_channel.oos_report(item).then(function (s)
                                {
                                    client.setUIscreen(client, "message");
                                })
                        })
                })
        })

        $("#message_oos-btn").on('click', function(e)
                {
                    $("#message_oos-list").empty();
                    $("#message_oos-search").val("");
                });
        $("#mainCarousel").on('slide.bs.carousel', function (e)
                {
                    if ($(e.relatedTarget).attr('id') === 'chart')
                    {
                        var data = [];
                        Object.keys(client.bcstats).forEach(function (barcode)
                            {
                                data.push(client.bcstats[barcode]);
                            })
                        var w = $("#mainCarousel").width();
                        var h = $("#mainCarousel").height();
                        d3.select("#chart").select("svg").remove();
                        var svg = d3.select("#chart")
                            .append("svg")
                            .attr("width", w)
                            .attr("height", 500);
                        svg.selectAll("rect")
                            .data(data)
                            .enter()
                            .append("rect")
                            .attr("x", function(d,i) {
                                return i * (w  / data.length);
                            })
                            .attr("y", function(d) {
                                return h - d;
                            })
                            .attr("width", 20)
                            .attr("height", function(d) {
                                return d
                            });
                    }
                });
    }


    constructor(type: ClientType, id: number) {
        this.type = type;
        this.id = id;

        this.timeout_timer = null;
    }
}

$(document).ready(function() {
    var client = new Client(ClientType.Soda, 0);
    client.setup_ui(client);
    client.connect(client);
})
