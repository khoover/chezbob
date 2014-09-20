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

var log;

var InitData = (function () {
    function InitData() {
        this.prepareLogs = function (initdata, callback) {
            log = bunyan.createLogger({
                name: 'vdb-server',
                streams: [
                    {
                        stream: process.stdout,
                        level: "debug"
                    }
                ]
            });
            log.level("debug");
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
        this.vdbport = "/dev/ttyS0";
        this.timeout = 10000;
        this.remote_endpoint = "http://127.0.0.1:8080/api";
        this.rpc_port = 8083;
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
                log.info("vdb_server version " + initdata.longVersion);
                callback();
            };
        }(initdata));
    };
    return InitData;
})();

var vdb_server = (function () {
    function vdb_server(initdata) {
        var _this = this;
        //asynchronusly sends a string and returns the result in a callback
        //a timeout occurs if data is not returned within the timeout.
        this.sendread = function (data, cb) {
            if (_this.solicit) {
                //already someone waiting, fail
                log.warn("Sendread failed, request in progress");
                cb("Request in progress, please try again!", null);
            } else {
                _this.solicit = true;
                _this.solicit_cb = cb;
                _this.solicit_tm = setTimeout(function (vdb) {
                    return function () {
                        log.error("sendread request failed, timeout!");
                        vdb.solicit_cb = null;
                        vdb.solicit_tm = null;
                        vdb.solicit = false;
                        cb("Request timed out!", null);
                    };
                }(_this), _this.initdata.timeout);

                _this.send(data, null);
            }
        };
        //asynchrnously sends a string over port
        this.send = function (data, cb) {
            log.debug("send: ", jsesc(data));
            _this.port.write(data, function (error) {
                if (typeof error !== 'undefined' && error && error !== null) {
                    log.error("Couldn't write to serial port, " + error);
                }
                if (typeof cb !== 'undefined' && cb) {
                    cb(error);
                }
            });
        };
        this.start = function () {
            log.info("vdb_server starting, listening on " + _this.initdata.vdbport);
            _this.port = new serialport(_this.initdata.vdbport);
            _this.port.on("open", function (vdb) {
                return function () {
                    log.debug("serial port successfully opened.");
                    vdb.port.on('data', function (data) {
                        //it is highly unlikely that we got more than
                        //1 byte, but if we did, make sure to process
                        //each byte
                        var process_last = false;
                        for (var i = 0; i < data.length; i++) {
                            switch (data[i]) {
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
                                    vdb.current_buffer += data.toString('utf8', i, i + 1);
                            }
                        }
                        if (process_last) {
                            //if this is a solicited request, clear the timer and
                            //call the callback
                            if (vdb.solicit) {
                                var cb_temp = vdb.solicit_cb;
                                vdb.solicit_cb = null;
                                vdb.solicit = false;
                                clearTimeout(vdb.solicit_tm);
                                cb_temp(null, vdb.last_buffer);
                            } else {
                                switch (vdb.last_buffer[0]) {
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
                                    default:
                                        log.warn("Unhanded CLINK request " + vdb.last_buffer);
                                }
                                // else
                                //{
                                //otherwise send to the remote endpoint.
                                //vdb.rpc_client.request("Soda.remotevdb", data, function (err, response)
                                //        {
                                //           if (err)
                                //          {
                                //             log.error("Error contacting remote endpoint", err);
                                //        }
                                //       else
                                //      {
                                //         log.debug("remotevdb successful, response=", response);
                                //    }
                                //  });
                                //}
                            }
                        }
                    });
                    vdb.reset(vdb);
                    var server = jayson.server({
                        "Vdb.command": function (vdb) {
                            return function (command, callback) {
                                log.debug("remote request: " + command);
                                vdb.sendread(command, function (err, result) {
                                    callback(err, result);
                                });
                            };
                        }(vdb)
                    });
                    server.http().listen(vdb.initdata.rpc_port);
                    log.info("rpc endpoint listening on port " + vdb.initdata.rpc_port);
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
    //sends the commands to reset the vdb device
    vdb_server.prototype.reset = function (vdb) {
        async.series([
            function (cb) {
                vdb.send("\n\n\n\n\r", cb);
            },
            function (cb) {
                vdb.sendread("\x1B\r", cb);
            },
            function (cb) {
                vdb.sendread("W090001\r", cb);
            },
            function (cb) {
                vdb.sendread("W070001\r", cb);
            },
            function (cb) {
                vdb.sendread("WFF0000\r", cb);
            }
        ], function (error, result) {
            if (error !== null) {
                log.info("Vending machine interface successfully reset.", result);
            }
        });
    };
    return vdb_server;
})();
var App = (function () {
    function App() {
    }
    App.prototype.main = function (args) {
        this.initdata = new InitData();
        this.initdata.init(this.initdata, function (err, res) {
            var vdb = new vdb_server(res);
            vdb.start();
        });
    };
    return App;
})();
exports.App = App;
