/// <reference path="../typings/tsd.d.ts"/>

var git = require('git-rev-2');
import async = require('async');
var pkginfo = require('pkginfo')(module);
var http = require('http');
var repl = require('repl');
var stream = require('stream');
var util = require('util');
var bunyan = require('bunyan');
var serialport = require('serialport').SerialPort;
var jayson = require('jayson');
import Buffer = require('buffer');
var jsesc = require('jsesc');
var bunyanredis = require('bunyan-redis');

var log;
var ringbuffer;
var redistransport;

class InitData {
    version: String;
    longVersion: String;

    mdbport: String;
    timeout: Number;
    remote_endpoint: String;
    rpc_port: number;
    event_mode: boolean;
    config;

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
                log.info("mdb_server version " + initdata.longVersion);
                callback();
            }
        }(initdata))
    }

    prepareLogs = (initdata: InitData, callback: () => void) : void =>
    {
        ringbuffer = new bunyan.RingBuffer({ limit: 1000 });
        redistransport = new bunyanredis( {
            container: 'cb_log',
            host: '127.0.0.1',
            port: 6379,
            db: 0,
            length: 5000
        });
        log = bunyan.createLogger(
                {
                    name: 'mdb-server',
                    streams: [
                    {
                        stream: process.stdout,
                        level: "trace"
                    },
                    {
                        level: "trace",
                        type: "raw",
                        stream: ringbuffer
                    },
                    {
                        level: "trace",
                        type: "raw",
                        stream: redistransport
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
        if (args.length < 1)
        {
            this.config = require("/etc/chezbob.json");
        }
        else
        {
            this.config = require(args[0]);
        }

        this.mdbport = this.config.mdbd.device;
        this.timeout = this.config.mdbd.timeout;
        this.remote_endpoint = this.config.sodad.endpoint;
        this.rpc_port = this.config.mdbd.port;
        this.event_mode = this.config.mdbd.event_mode;
    }
}

class mdb_server {
    initdata : InitData; //initialization data

    current_buffer; //current data being read in
    port; // open port
    rpc_client;

    //sends the commands to reset the mdb device
    reset (mdb : mdb_server) {
        async.series([
                // Reset the coin changer
                function (cb) { mdb.sendread("R1", cb); },
                function (cb) { mdb.sendread("N FFFF", cb); },
                function (cb) { mdb.sendread("M FFFF", cb); },
                function (cb) { mdb.sendread("P1", cb); },
                function (cb) { mdb.sendread("E1", cb); },
                // Reset the bill reader
                function (cb) { mdb.sendread("R2", cb); },
                function (cb) { mdb.sendread("P2", cb); },
                function (cb) { mdb.sendread("L FFFF", cb); },
                function (cb) { mdb.sendread("V 0000", cb); },
                function (cb) { mdb.sendread("J FFFF", cb); },
                function (cb) { mdb.sendread("S7", cb); }
                //function (cb) { mdb.sendread("E2", cb); }
                ],
                function (error, result)
                {
                    if (error !== null)
                    {
                        log.info("Coin reader and bill reader successfully reset.", result);
                    }
                }
                );
    }

    //asynchronusly sends a string and returns the result in a callback
    //a timeout occurs if data is not returned within the timeout.
    sendread = (data: String, cb) =>
    {
        this.send(data, null);
    }

    //asynchrnously sends a string over port
    send = (data: String, cb) => {
        log.debug("send: ", data);
        this.port.write(data + '\r', function(error)
                {
                    if (typeof error !== 'undefined' && error && error !== null)
                    {
                        log.error("Couldn't write to serial port, " + error);
                    }
                    if (typeof cb !== 'undefined' && cb)
                    {
                        cb(error);
                    }
                })
    }

    start = () => {
        log.info("mdb_server starting, listening on " + this.initdata.mdbport);
        this.port = new serialport(this.initdata.mdbport);
        this.port.on("open", function(mdb: mdb_server){ return function ()
                {
                    log.debug("serial port successfully opened.");
                    mdb.port.on('data', function(data : Buffer)
                    {
                        //it is highly unlikely that we got more than
                        //1 byte, but if we did, make sure to process
                        //each byte
                        for (var i : number = 0; i < data.length; i++)
                        {
                            //treat the port as an EventEmitter, have listeners for
                            //certain types of messages on it.
                            switch (data[i])
                            {
                                case 0xa:
                                    log.debug("received ACK");
                                    process.nextTick(function () {
                                        mdb.port.emit('ACK');
                                    });
                                    break;
                                case 0xd:
                                    log.debug("received " + mdb.current_buffer);
                                    process.nextTick((function (message: String) { return function () {
                                        if (message.length === 1)
                                        {
                                            mdb.port.emit(message);
                                        }
                                        else
                                        {
                                            mdb.port.emit(message.slice(0, 2), message);
                                        }
                                    }})(mdb.current_buffer));
                                    mdb.current_buffer = "";
                                    break;
                                default:
                                    mdb.current_buffer += data.toString('utf8', i, i+1);
                            }
                        }
                    });
                    if (mdb.initdata.event_mode)
                    {
                        //add listener for bill escrow messages
                        mdb.port.on('Q1', function (message: String) {
                        });
                        //add listener for coin deposit messages
                        mdb.port.on('P1', function (message: String) {
                        });
                        //add listener for logout button
                        mdb.port.on('W', function () {
                        });
                    }
                    else
                    {
                        //add polling calls to the bill and change acceptors
                    }
                            if (process_last)
                            {
                                if (mdb.last_buffer[0] != "X")
                                {
                                //send to the remote endpoint.
                                mdb.rpc_client.request("Soda.remotemdb", [mdb.last_buffer], function (err, response)
                                        {
                                            if (err)
                                            {
                                                log.error("Error contacting remote endpoint", err);
                                            }
                                            else
                                            {
                                                log.debug("remotemdb successful, response=", response);
                                            }
                                        });
                                }
                                else
                                {
                                    log.trace("Error ignored: " + mdb.last_buffer);
                                }
                            }
                    mdb.reset(mdb);
                    var server = jayson.server(
                            {
                                "Mdb.command": function(mdb : mdb_server) { return function (command: String, callback)
                                {
                                    log.debug("remote request: " + command);
                                    mdb.sendread(command, function(err, result)
                                        {
                                            callback(err, result);
                                        });
                                }}(mdb),
                                "Mdb.logs": function (callback)
                                {
                                    callback(null, ringbuffer.records);
                                }
                            }
                            )
                    server.http().listen(mdb.initdata.rpc_port);
                    log.info("rpc endpoint listening on port " + mdb.initdata.rpc_port);
                }}(this));
        this.port.on("error", function (error)
                {
                    log.error("Fatal serial port error - " + error);
                    process.exit(1);
                });
    }

    constructor(initdata : InitData) {
        this.initdata = initdata;
        this.current_buffer = "";
        this.rpc_client = jayson.client.http(initdata.remote_endpoint);
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
                    var mdb = new mdb_server(res);
                    mdb.start();
                }
                );
    }

    constructor () {}
}
