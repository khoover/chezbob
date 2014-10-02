/// <reference path="../typings/tsd.d.ts"/>

import $ = require("jquery");
jQuery = $;
import Q = require("q");
import io = require("socket.io");
var rpc = require("rpc");
var bootstrap = require("bootstrap");

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

    connect(client: Client)
    {
        rpc.connect(window.location.protocol + '//' + window.location.hostname + ':' + window.location.port);
        rpc.loadChannel('serverChannel').then(
                function (channel)
                {
                    client.server_channel = channel;
                    client.log = new ClientLogger(channel);
                    client.log.info("New client connected");
                    channel.barcode('342450').then(function (val)
                    {
                        client.log.info(val.name);
                    }).catch(function (err)
                    {
                        client.log.error(err);
                    })


                }
                )
    }

    setup_ui(client: Client)
    {
        $("#dologin").on("click", function() {
            client.server_channel.authenticate(0,0, $("#username").val(), $("#password").val()).then(
                function (val)
                {
                    client.log.info(val);
                }
                ).catch(function(err)
                    {
                        client.log.error(err);
                    }
                )
        });
    }
    constructor(type: ClientType, id: number) {

    }
}

$(document).ready(function() {
    var client = new Client(ClientType.Soda, 0);
    client.setup_ui(client);
    client.connect(client);
})
