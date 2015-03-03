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

var libfprint = require('node-libfprint');
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

    type = 0;
    id = 0;

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
                log.info("fp_server version " + initdata.longVersion);
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
                    name: 'fp-server',
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
        }
        else
        {
        }
        this.timeout = 1000;
        this.remote_endpoint = "http://127.0.0.1:8080/api";
        this.rpc_port = 8089;
    }
}

class fp_server {
    initdata : InitData; //initialization data

    solicit: boolean; //whether or not current_buffer was solicited
    solicit_cb; //callback for a solicitation
    solicit_tm; //timer for solicitation timeout
    last_buffer;
    current_buffer: Buffer; //current data being read in
    current_length;

    port; // open port
    rpc_client;

    reader;


    //sends the commands to reset the fp reader
    reset (server : fp_server) {
        async.series([
                ],
                function (error, result)
                {
                    if (error !== null)
                    {
                        log.info("fingerprint reader successfully reset.", result);
                    }
                }
                );
    }

    start (server: fp_server) {
        log.info("fp_server starting, listening on " + server.initdata.rpc_port);
        //use first available reader (TODO: support multiple readers? "umm... no" - Brown )
        var fp = new libfprint.fprint();
        fp.init();
        var reader = fp.discover()[0];
        log.info("Using reader " + reader.driver_detail);
        server.reader = promise.promisifyAll(fp.get_reader(reader.handle));

        // default to identify mode
        // ****TODO****

        var jserver = jayson.server(
                {
                    // Upon receiving fp.enroll, start enrolling a fingerprint
                    "fp.enroll" : function (uid, callback)
                    {
                        log.info("Begin fingerprint enroll for uid " + uid);
                        // start the reader enrolling
                        server.reader.start_enrollAsync().then(
                                function (result)
                                {
                                    log.info("SUCCESS: fingerprint enroll for uid " + uid);

                                    // TODO send all the data back to the server for storage
                                    var jresult = {

                                        // image of print
                                        fpimage : result[2].toString('base64'),
                                        // height of image
                                        height : result[3],
                                        // width of image
                                        width : result[4]
                                        
                                    }
                                    callback(null, jresult);
                                }
                            )
                            .catch(function (err)
                                {
                                    log.error("Fingerprint enroll for uid " + uid + " FAILED, reason= " + err);
                                    callback(err);
                                })
                    },
                    // Upon receiving fp.stopenroll, stop whatever enrollment may be occuring
                    "fp.stopenroll" : function (uid)
                    {
                        log.info("Stop fingerprint enroll for uid " + uid);
                        // stop the reader enrolling
                        server.reader.stop_enrollAsync().then(
                                function()
                                {
                                    log.info("SUCCESS: fingerprint stop enroll for uid " + uid);
                                }
                            )
                    },
                    // TODO
                    "fp.identify" : function (callback)
                    {
                        log.info("Begin fingerprint identify");
                        server.reader.start_identifyAsync().then(
                                function(result)
                                {
                                    var jresult = {
                                        fpimage : result[2].toString('base64'),
                                        height : result[3],
                                        width : result[4]
                                    }
                                    callback(null, jresult);
                                }
                            )
                            .catch(function (err)
                                {
                                    log.error("Fingerprint identify FAILED, reason= " + err);
                                    callback(err);
                                })
                    },
                    "fp.stopidentify" : function ()
                    {
                        log.info("Stop fingerprint identify");
                        server.reader.stop_identifyAsync().then(
                                function()
                                {
                                    log.info("SUCCESS: fingerprint stop identify");
                                }
                            )
                    }
                }
                )
            jserver.http().listen(server.initdata.rpc_port);
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
                    var fp = new fp_server(res);
                    fp.start(fp);
                }
                );
    }

    constructor () {}
}
