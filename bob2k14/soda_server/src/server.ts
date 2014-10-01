/// <reference path="../typings/tsd.d.ts"/>

var git = require('git-rev-2');
import async = require('async');
var pkginfo = require('pkginfo')(module);
var http = require('http');
var repl = require('repl');
var stream = require('stream');
var util = require('util');
var bunyan = require('bunyan');
var jayson = require('jayson');
var jsesc = require('jsesc');
import Buffer = require('buffer');
import express = require('express')
var bunyanredis = require('bunyan-redis');
var io = require('socket.io');
var promise = require('bluebird');
var rpc = require('socket.io-rpc');

var config = require('/etc/chezbob.json');

var log;
var ringbuffer;
var redistransport;

class InitData {
    version: String;
    longVersion: String;

    timeout: Number;

    loadVersion (initdata: InitData, callback: () => void) : void
    {
        log.debug("Getting version information...");
        initdata.version = module.exports.version;
        initdata.longVersion = module.exports.version;
        //if we are in a git checkout, append the short SHA.
        git.short(__dirname, function (initdata: InitData) {
            return function (err, str)
            {
                if (err === null)
                {
                    log.debug("Git checkout detected.");
                    initdata.version += "+";
                    initdata.longVersion += "/" + str;
                }
                log.info("sodad_server version " + initdata.longVersion);
                callback();
            }
        }(initdata))
    }

    prepareLogs = (initdata: InitData, callback: () => void) : void =>
    {
        ringbuffer = new bunyan.RingBuffer({ limit: 1000 });
        redistransport = new bunyanredis({
            container: 'cb_log',
            host: '127.0.0.1',
            port: 6379,
            db: 0,
            length: 5000
        });
        log = bunyan.createLogger(
                {
                    name: 'sodad-server',
                    streams: [
                    {
                        stream: process.stdout,
                        level: "info"
                    },
                    {
                        stream: ringbuffer,
                        level: "trace"
                    },
                    {
                        stream: redistransport,
                        type: "raw",
                        level: "trace"
                    }
                    ]
                }
                );
        log.info("Logging system initialized");
        callback();
    }

    init = (initdata : InitData, callback: (err,res) => void) : void =>
    {
        async.series([
                    function (cb) {initdata.prepareLogs(initdata, cb)},
                    function (cb) {initdata.loadVersion(initdata, cb)},
                    function (err, res)
                    {
                        callback(null, initdata);
                    }
                ]);
    }

    constructor(args: string[]) {
        this.timeout = 10000;
    }
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

class sodad_server {
    initdata : InitData; //initialization data
    app;
    server;
    clientloggers;

    start = () => {
        log.info("sodad_server starting, listening on " + config.sodad.port);
        this.app = express();

        //configure routes
        this.app.use('/ui', express.static(__dirname + '/ui'));

        this.app.get('/', function (req,res) {
            log.trace("Handling request: ", req);
            res.send("hello world.");
        });

        this.server = this.app.listen(config.sodad.port, function() {

        });


        rpc.createServer(io.listen(this.server), this.app);
        rpc.expose('serverChannel',{
            log: function(level: log_level, data)
            {
                switch(level)
                {
                    case log_level.TRACE:
                        log.trace(data);
                        break;
                    case log_level.DEBUG:
                        log.debug(data);
                        break;
                    case log_level.INFO:
                        log.info(data);
                        break;
                    case log_level.WARN:
                        log.warn(data, {client: this.id});
                        break;
                    case log_level.ERROR:
                        log.error(data);
                        break;
                    case log_level.FATAL:
                        log.fatal(data);
                }
            }
        });
/*
        io.listen(this.server).sockets.on('connection', function(socket)
        {
            log.info("Connected.");
        });
        */
    }

    constructor(initdata : InitData) {
        this.initdata = initdata;
    }
}
export class App {
    private initdata : InitData;

    main(args: string[])
    {
        this.initdata = new InitData(args);
        this.initdata.init(this.initdata,
                function (err, res: InitData)
                {
                    var sodad = new sodad_server(res);
                    sodad.start();
                }
                );
    }

    constructor () {}
}
