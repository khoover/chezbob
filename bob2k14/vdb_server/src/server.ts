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
var jsesc = require('jsesc');
import Buffer = require('buffer');
var bunyanredis = require('bunyan-redis');

var log;
var ringbuffer;
var redistransport;

class InitData {
    version: String;
    longVersion: String;

    vdbport: String;
    timeout: Number;
    remote_endpoint: String;
    rpc_port: number;

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
                log.info("vdb_server version " + initdata.longVersion);
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
        })
        log = bunyan.createLogger(
                {
                    name: 'vdb-server',
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
                        level: "trace",
                        type: "raw"
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
            this.vdbport = "/dev/ttyS0";
        }
        else
        {
            this.vdbport = args[0];
        }

        this.timeout = 10000;
        this.remote_endpoint = "http://127.0.0.1:8080/api";
        this.rpc_port = 8083;
    }
}

class vdb_server {
    initdata : InitData; //initialization data

    solicit: boolean; //whether or not current_buffer was solicited
    solicit_cb; //callback for a solicitation
    solicit_tm; //timer for solicitation timeout
    last_buffer;
    current_buffer; //current data being read in
    port; // open port
    rpc_client;
    authorize_vend: boolean;
    current_vend: string; //currently vending soda

    //sends the commands to reset the vdb device
    reset (vdb : vdb_server) {
        async.series([
                // Clear any outstanding messages
                function (cb) { vdb.send("\n\n\n\n\r", cb); },
                // Reset the interface
                function (cb) { vdb.sendread("\x1B\r", cb); },
                function (cb) { vdb.sendread("W090001\r", cb); },
                function (cb) { vdb.sendread("W070001\r", cb); },
                function (cb) { vdb.sendread("WFF0000\r", cb); }
                ],
                function (error, result)
                {
                    if (error !== null)
                    {
                        log.info("Vending machine interface successfully reset.", result);
                    }
                }
                );
    }

    //asynchronusly sends a string and returns the result in a callback
    //a timeout occurs if data is not returned within the timeout.
    sendread = (data: String, cb) =>
    {
        if (this.solicit)
        {
            //already someone waiting, fail
            log.warn("Sendread failed, request in progress");
            cb("Request in progress, please try again!", null);
        }
        else
        {
            this.solicit = true;
            this.solicit_cb = cb;
            this.solicit_tm = setTimeout(function(vdb:vdb_server){return function() {
                log.error("sendread request failed, timeout!");
                vdb.solicit_cb = null;
                vdb.solicit_tm = null;
                vdb.solicit = false;
                cb("Request timed out!", null);
            }}(this), this.initdata.timeout);


            this.send(data, null);
        }
    }

    //asynchrnously sends a string over port
    send = (data: String, cb) => {
        log.debug("send: ", jsesc(data));
        this.port.write(data, function(error)
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
        log.info("vdb_server starting, listening on " + this.initdata.vdbport);
        this.port = new serialport(this.initdata.vdbport);
        this.port.on("open", function(vdb: vdb_server){ return function ()
                {
                    log.debug("serial port successfully opened.");
                    vdb.port.on('data', function(data : Buffer)
                        {
                            //it is highly unlikely that we got more than
                            //1 byte, but if we did, make sure to process
                            //each byte
                            var process_last : boolean = false;
                            for (var i : number = 0; i < data.length; i++)
                            {
                                switch (data[i])
                                {
                                    case 0xa:
                                        log.debug("received ACK");
                                    break;
                                    case 0xd:
                                        vdb.last_buffer = vdb.current_buffer;
                                        vdb.current_buffer = "";
                                        vdb.send("\n", null);
                                        log.debug("received " + vdb.last_buffer);
                                        //mark that we need to send the last buffer
                                        process_last = true;
                                        break;
                                    default:
                                        vdb.current_buffer += data.toString('utf8', i, i+1);
                                }
                            }
                            if (process_last)
                            {
                                //if this is a solicited request, clear the timer and
                                //call the callback
                                if (vdb.solicit)
                                {
                                    var cb_temp = vdb.solicit_cb;
                                    vdb.solicit_cb = null;
                                    vdb.solicit = false;
                                    clearTimeout(vdb.solicit_tm);
                                    cb_temp(null, vdb.last_buffer);
                                }
                                else
                                {
                                    //otherwise, check if it's something we automatically handle
                                    switch (vdb.last_buffer[0])
                                    {
                                        case "F":
                                            //CLINK: Card reader disable
                                            vdb.send("X\r", null); //ack
                                            break;
                                        case "G":
                                            //CLINK: Card reader enable
                                            vdb.send("X\r", null); //ack
                                            break;
                                        case "M":
                                            //CLINK: Poll
                                            vdb.send("C\r", null); //card present
                                            break;
                                        case "H":
                                            //CLINK: VMC Session end
                                            vdb.send("X\r", null); //ack
                                            break;
                                        case "R":
                                            //CLINK: Request Authorization (timeout=5000)
                                            vdb.current_vend = vdb.last_buffer.substring(9,11);
                                            vdb.rpc_client.request("Soda.vdbauth", [vdb.current_vend], function (err, response)
                                                    {
                                                        log.debug("Response from cb ", response);
                                                        if (err)
                                                        {
                                                            vdb.send("D\r", null);
                                                            log.error("Error requesting authorization for row " + vdb.current_vend +  ": ", err);
                                                        }
                                                        else if (response.result === true)
                                                        {
                                                            vdb.send("A\r", null);
                                                            log.info("Authorizing vend for row " + vdb.current_vend);
                                                        }
                                                        else
                                                        {
                                                            vdb.send("D\r", null);
                                                            log.info("Denying vend for row " + vdb.current_vend);
                                                        }
                                                    }
                                                    );
                                            break;
                                        case "K":
                                            //CLINK: Vend OK
                                            vdb.send("X\r", null); //ack
                                            vdb.rpc_client.request("Soda.vdbvend", [true, vdb.current_vend], function(err, response)
                                                    {
                                                         if (err)
                                                        {
                                                            log.error("Error sending vend success result to RPC endpoint!");
                                                        }
                                                    });
                                            log.info("Vend success, row ", vdb.current_vend);
                                            break;
                                        case "L":
                                            //CLINK: Vend FAIL
                                            vdb.send("X\r", null);
                                            vdb.rpc_client.request("Soda.vdbvend", [false, vdb.current_vend], function(err,response)
                                                    {
                                                        if (err)
                                                        {
                                                            log.error("Error sending vend fail result to RPC endpoint!");
                                                        }
                                                    }
                                                    );
                                            log.info("Vend failure, row", vdb.current_vend);
                                            break;
                                        default:
                                            log.warn("Unhanded CLINK request " + vdb.last_buffer);
                                    }
                                }
                            }
                        });
                    vdb.reset(vdb);
                    var server = jayson.server(
                            {
                                "Vdb.command": function(vdb : vdb_server) { return function (command: String, callback)
                                {
                                    log.debug("remote request: " + command);
                                    vdb.sendread(command, function(err, result)
                                        {
                                            callback(err, result);
                                        });
                                }}(vdb),
                                "Vdb.logs": function (callback) {
                                    callback(null, ringbuffer.records);
                                }
                            }
                            )
                    server.http().listen(vdb.initdata.rpc_port);
                    log.info("rpc endpoint listening on port " + vdb.initdata.rpc_port);
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
        this.solicit_cb = null;
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
                    var vdb = new vdb_server(res);
                    vdb.start();
                }
                );
    }

    constructor () {}
}
