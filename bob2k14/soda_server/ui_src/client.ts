/// <reference path="../typings/tsd.d.ts"/>

import $ = require("jquery");
import Q = require("q");
import io = require("socket.io");
var rpc = require("rpc");

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

    connect = () =>
    {
        rpc.connect(window.location.protocol + '//' + window.location.hostname + ':' + window.location.port);
        rpc.loadChannel('serverChannel').then(
                function (channel)
                {
                    this.server_channel = channel;
                    this.log = new ClientLogger(channel);
                    this.log.warn("uhoh.");
                    this.log.warn("mmmmm")
                }
                )
    }

    constructor(type: ClientType, id: number) {

    }
}

$(document).ready(function() {
    var client = new Client(ClientType.Soda, 0);
    client.connect();
})
