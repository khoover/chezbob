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
var bunyanredis = require('bunyan-redis');
var promise = require('bluebird');
var fs = promise.promisifyAll(require('fs'));

var log;
var ringbuffer;
var redistransport;

var keycode = {};
keycode[2] = "1";
keycode[3] = "2";
keycode[4] = "3";
keycode[5] = "4";
keycode[6] = "5";
keycode[7] = "6";
keycode[8] = "7";
keycode[9] = "8";
keycode[10] = "9";
keycode[11] = "0";

class InitData {
    version: String;
    longVersion: String;

    barcodeport: String;
    timeout: Number;
    remote_endpoint: String;
    rpc_port: number;

    type = 0;
    id = 0;
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
                log.info("barcodei_server version " + initdata.longVersion);
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
                    name: 'barcodei-server',
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
            this.config = require(args[0]);
        }
        this.barcodeport = this.config.barcodeid.device
        this.timeout = this.config.barcodeid.timeout;
        this.remote_endpoint = this.config.sodad.endpoint;
        this.rpc_port = this.config.barcodeid.port
    }
}

class barcodei_server {
    initdata : InitData; //initialization data

    solicit: boolean; //whether or not current_buffer was solicited
    solicit_cb; //callback for a solicitation
    solicit_tm; //timer for solicitation timeout
    last_buffer;
    current_buffer: Buffer; //current data being read in
    current_length;

    port; // open port
    rpc_client;



    //sends the commands to reset the barcode reader
    reset (server : barcodei_server) {
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

    scan_barcode(server: barcodei_server, barcode: string)
    {
        log.info("Barcode scanned: ", barcode);
        server.rpc_client.requestAsync("Soda.remotebarcode", [server.initdata.type, server.initdata.id, null, barcode])
            .then(function (response)
                    {
                        log.trace("Remote barcode rpc successful, response=", response);
                    })
            .catch(function(err)
                    {
                        log.error("Remote barcode rpc failed, reason=", err);
                    })
    }

    parse(server: barcodei_server, buffer: Buffer)
    {
        var decoded;
        if (buffer.readUInt16LE(16) === 1)
        {
            decoded = {
                time_s: buffer.readUInt32LE(0), //NB: These are actually 64-bit but we don't need them... so I don't bother reading them
                time_ms: buffer.readUInt32LE(8), //and for those who care, js numbers are double floats so 64-bit uints wouldn't work anyway.
                keycode: buffer.readUInt16LE(18),
                type: buffer.readUInt16LE(20)
            }

            if (decoded.type === 0) //key up
            {
                if (decoded.keycode === 28)
                {
                    //enter key
                    server.scan_barcode(server, server.last_buffer);
                    server.last_buffer = "";
                }
                else
                {
                    server.last_buffer += String(keycode[decoded.keycode]);
                }
                log.info("Decode ", decoded.keycode);
            }
        }
    }

    startRead (server: barcodei_server, fd)
    {
        fs.readAsync(fd, server.current_buffer, 0, server.current_length, null)
            .then(function(len)
                    {
                        var ev = server.parse(server, server.current_buffer);
                        return server.startRead(server, fd);
                    })
    }

    start (server: barcodei_server) {
        log.info("barcodei_server starting, listening on " + server.initdata.barcodeport);
        fs.openAsync(server.initdata.barcodeport, 'r')
            .then(function (fd)
                    {
                        return server.startRead(server, fd);
                    })
            .catch(function (e)
                    {
                        log.error("Error :" + e);
                    });
    }

    constructor(initdata : InitData) {
        this.initdata = initdata;
        this.current_length = 24;
        this.current_buffer = new Buffer(this.current_length);
        this.last_buffer = "";
        this.solicit_cb = null;
        this.rpc_client = promise.promisifyAll(jayson.client.http(initdata.remote_endpoint));
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
                    var barcode = new barcodei_server(res);
                    barcode.start(barcode);
                }
                );
    }

    constructor () {}
}
