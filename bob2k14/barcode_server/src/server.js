/// <reference path="../typings/tsd.d.ts"/>
var git = require('git-rev-2');
var async = require('async');
var pkginfo = require('pkginfo')(module);
var http = require('http');
var repl = require('repl');
var stream = require('stream');
var util = require('util');
var bunyan = require('bunyan');
var serialport = require('serialport').SerialPort;
var jayson = require('jayson');

var jsesc = require('jsesc');
var bunyanredis = require('bunyan-redis');

var log;
var ringbuffer;
var redistransport;

var InitData = (function () {
    function InitData(args) {
        this.prepareLogs = function (initdata, callback) {
            ringbuffer = new bunyan.RingBuffer({ limit: 1000 });
            redistransport = new bunyanredis({
                container: 'cb_log',
                host: '127.0.0.1',
                port: 6379,
                db: 0,
                length: 5000
            });
            log = bunyan.createLogger({
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
            });
            log.info("Logging system initialized");
            callback();
        };
        this.init = function (initdata, callback) {
            async.series([
                function (cb) {
                    initdata.prepareLogs(initdata, cb);
                },
                function (cb) {
                    initdata.loadVersion(initdata, cb);
                },
                function (err, res) {
                    callback(null, initdata);
                }
            ]);
        };
        if (args.length < 1) {
            this.barcodeport = "/dev/barcode";
        } else {
            this.barcodeport = args[0];
        }
        this.timeout = 1000;
        this.remote_endpoint = "http://127.0.0.1:8080/api";
        this.rpc_port = 8086;
    }
    InitData.prototype.loadVersion = function (initdata, callback) {
        log.debug("Getting version information...");
        initdata.version = module.exports.version;
        initdata.longVersion = module.exports.version;

        //if we are in a git checkout, append the short SHA.
        git.short(__dirname, function (initdata) {
            return function (err, str) {
                if (err === null) {
                    log.debug("Git checkout detected.");
                    initdata.version += "+";
                    initdata.longVersion += "/" + str;
                }
                log.info("barcode_server version " + initdata.longVersion);
                callback();
            };
        }(initdata));
    };
    return InitData;
})();

var barcode_server = (function () {
    function barcode_server(initdata) {
        var _this = this;
        this.start = function () {
            log.info("barcode_server starting, listening on " + _this.initdata.barcodeport);
            _this.port = new serialport(_this.initdata.barcodeport);
            _this.current_length = null;
            _this.port.on("open", function (barcode) {
                return function () {
                    log.debug("serial port successfully opened.");
                    barcode.port.on('data', function (data) {
                        //it is highly unlikely that we got more than
                        //1 byte, but if we did, make sure to process
                        //each byte
                        var process_last = false;
                        for (var i = 0; i < data.length; i++) {
                            switch (data[i]) {
                                case 0xd:
                                    barcode.last_buffer = barcode.current_buffer;
                                    barcode.current_buffer = "";

                                    //mark that we need to send the last buffer
                                    process_last = true;
                                    barcode.current_length = null;
                                    break;
                                default:
                                    if (barcode.current_length === null) {
                                        barcode.current_length = data.readUInt8(i);
                                        if (barcode.current_length != 0) {
                                            log.trace("Ignoring command from reader");
                                            barcode.current_length = barcode.current_length + 1;
                                        }
                                    } else if (barcode.current_length == 0) {
                                        barcode.current_buffer += data.toString('utf8', i, i + 1);
                                    } else {
                                        barcode.current_length--;
                                        if (barcode.current_length == 0) {
                                            barcode.current_length = null;
                                        }
                                    }
                            }
                        }

                        if (process_last) {
                            log.info("Barcode scanned, type=" + barcode.last_buffer[0] + " barcode=" + barcode.last_buffer.substr(1));
                            barcode.rpc_client.request("Soda.remotebarcode", [barcode.last_buffer[0], barcode.last_buffer.substr(1)], function (err, response) {
                                if (err) {
                                    log.error("Error contacting remote endpoint", err);
                                } else {
                                    log.debug("remotebarcode successful, response=", response);
                                }
                            });
                            process_last = false;
                        }
                    });
                    barcode.reset(barcode);
                    var server = jayson.server({
                        "Barcode.logs": function (callback) {
                            callback(null, ringbuffer.records);
                        }
                    });
                    server.http().listen(barcode.initdata.rpc_port);
                    log.info("rpc endpoint listening on port " + barcode.initdata.rpc_port);
                };
            }(_this));
            _this.port.on("error", function (error) {
                log.error("Fatal serial port error - " + error);
                process.exit(1);
            });
        };
        this.initdata = initdata;
        this.current_buffer = "";
        this.solicit_cb = null;
        this.rpc_client = jayson.client.http(initdata.remote_endpoint);
    }
    //sends the commands to reset the barcode reader
    barcode_server.prototype.reset = function (server) {
        async.series([], function (error, result) {
            if (error !== null) {
                log.info("barcode reader successfully reset.", result);
            }
        });
    };
    return barcode_server;
})();
var App = (function () {
    function App() {
    }
    App.prototype.main = function (args) {
        this.initdata = new InitData(args);
        this.initdata.init(this.initdata, function (err, res) {
            var barcode = new barcode_server(res);
            barcode.start();
        });
    };
    return App;
})();
exports.App = App;
