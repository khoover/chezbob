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
var fs = require('fs');

var log;
var ringbuffer;
var redistransport;

class InitData {
    version: String;
    longVersion: String;

    barcodeport: String;
    timeout: Number;
    remote_endpoint: String;
    rpc_port: number;

    id;
    type;
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
                log.info("barcode_server version " + initdata.longVersion);
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
                    name: 'barcode-server',
                    streams: [
                    {
                        stream: process.stdout,
                        level: "info"
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
            this.config = require(fs.realpathSync(args[0]));
        }
        var bd_conf = this.config.barcoded;
        this.barcodeport = bd_conf.device;
        this.timeout = bd_conf.timeout;
        this.remote_endpoint = this.config.sodad.endpoint
        this.rpc_port = bd_conf.port;
        this.id = 0;
        this.type = 1;
    }
}

class barcode_server {
    initdata : InitData; //initialization data

    solicit: boolean; //whether or not current_buffer was solicited
    solicit_cb; //callback for a solicitation
    solicit_tm; //timer for solicitation timeout
    last_buffer;
    current_buffer; //current data being read in
    current_length;

    port; // open port
    rpc_client;



    //sends the commands to reset the barcode reader
    reset (server : barcode_server) {
        async.series([
                ],
                function (error, result)
                {
                    if (error !== null)
                    {
                        log.info("barcode reader successfully reset.", result);
                    }
                }
                );
    }

    start = () => {
        log.info("barcode_server starting, listening on " + this.initdata.barcodeport);
        this.port = new serialport(this.initdata.barcodeport);
        this.current_length = null;
        this.port.on("open", function(barcode: barcode_server){ return function ()
                {
                    log.debug("serial port successfully opened.");
                    barcode.port.on('data', function(data : Buffer)
                        {
                            //it is highly unlikely that we got more than
                            //1 byte, but if we did, make sure to process
                            //each byte
                            var process_last : boolean = false;
                            for (var i : number = 0; i < data.length; i++)
                            {
                                switch (data[i])
                                {
                                    case 0xd:
                                        barcode.last_buffer = barcode.current_buffer;
                                        barcode.current_buffer = "";
                                        //mark that we need to send the last buffer
                                        process_last = true;
                                        barcode.current_length = null;
                                        break;
                                    default:
                                        if (barcode.current_length === null)
                                        {
                                            barcode.current_length = data.readUInt8(i);
                                            if (barcode.current_length != 0) {
                                                log.trace("Ignoring command from reader");
                                                barcode.current_length = barcode.current_length + 1;
                                            }
                                        }
                                        else if (barcode.current_length == 0)
                                        {
                                            barcode.current_buffer += data.toString('utf8', i, i+1);
                                        }
                                        else
                                        {
                                            barcode.current_length--;
                                            if (barcode.current_length == 0){ barcode.current_length = null; }
                                        }
                                }
                            }

                            if (process_last)
                            {
                                log.info("Barcode scanned, type=" + barcode.last_buffer[0] + " barcode=" +  barcode.last_buffer.substr(1));
                                barcode.rpc_client.request("Soda.remotebarcode", [barcode.initdata.type, barcode.initdata.id, barcode.last_buffer[0], barcode.last_buffer.substr(1)], function (err, response)
                                        {
                                            if (err)
                                            {
                                                log.error("Error contacting remote endpoint", err);
                                            }
                                            else
                                            {
                                                log.debug("remotebarcode successful, response=", response);
                                            }
                                        });
                                process_last = false;
                            }
                        });
                    barcode.reset(barcode);
                    var server = jayson.server(
                            {
                                "Barcode.logs": function (callback)
                                {
                                    callback(null, ringbuffer.records);
                                }
                            }
                            )
                    server.http().listen(barcode.initdata.rpc_port);
                    log.info("rpc endpoint listening on port " + barcode.initdata.rpc_port);
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
                    var barcode = new barcode_server(res);
                    barcode.start();
                }
                );
    }

    constructor () {}
}
