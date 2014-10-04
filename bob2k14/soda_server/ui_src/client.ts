/// <reference path="../typings/tsd.d.ts"/>

import $ = require("jquery");
jQuery = $;
import Q = require("q");
import io = require("socket.io");
var rpc = require("rpc");
var bootstrap = require("bootstrap");
var d3 = require('d3-browserify');

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
    time;

    type : ClientType;
    id;

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
                    client.time = client.time - 1;
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
    }

    setUIscreen(client: Client, screen: string)
    {
        $(".ui-screen").addClass('hidden');
        $("#" + screen).removeClass('hidden');
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
                        $("#purchases-table tbody").append("<tr><td>" + purchasedata.name + "</td><td>" + purchasedata.amount + "</td>");
                        client.setBalance(client, purchasedata.newbalance);
                        client.setUIscreen(client,"mainpurchase");
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

        $("#balancewarn").tooltip({
            title: "Your balance is negative. Please add funds to your account.",
            placement: 'bottom'
        });
        $("#logoutbtn").on('click', function() {
            client.server_channel.logout();
        });
        $("#moretimebtn").on('click', function() {
            client.time = client.time + 30;
        });
        $("#optionsbtn").on('click', function() {
            client.stopTimeout(client);
            client.setUIscreen(client, "options");
        });
        $("#optionsexitbtn").on('click', function() {
            client.setUIscreen(client, "mainpurchase");
        });
        $("#transactionsbtn").on('click', function() {
            client.setUIscreen(client, "transactions");
        });
        $("#transactionsexitbtn").on('click', function() {
            client.setUIscreen(client, "options");
        });
        $("#manualpurchasebtn").on('click', function() {
            client.setUIscreen(client, "manualpurchase");
        });
        $("#manualpurchaseexitbtn").on('click', function() {
            client.setUIscreen(client, "options");
        });
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
