/// <reference path="../typings/tsd.d.ts"/>
/// <reference path="models.ts"/>

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
var proc = require('process');

// DB access
var pgpass = require('pgpass');
var Models = require('./models');
var sequelize = require('sequelize');

// FP library
var libfprint = require('node-libfprint');

var log;
var ringbuffer;
var redistransport;

// DB variables
var dblog;
var ringbuffer;
var redistransport;
var sql;
var models;
var redisclient;

class InitData {
    version: String;
    longVersion: String;

    // DB variables
    dbname;
    dbuser;
    dbhost;
    config;

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

    // DB for FP access
    connectDB = (initdata : InitData, callback: () => void) : void  =>
    {
        dblog = log.child({module: 'db'});
        if (initdata.config.db.type == "postgres") {
            var sequelize = require('sequelize');

            log.info(proc.env);

            pgpass({host: this.dbhost,
                    user: this.dbuser}, function (password)
                    {
                        sql = new sequelize(initdata.dbname, initdata.dbuser, password,  {
                            host: initdata.dbhost,
                            dialect: 'postgres',
                            logging: function(data) {
                                dblog.trace(data);
                            }
                        })
                        models = new Models.Models(sql, "postgres");
                        log.info("Sequelize database initialized.")
                        callback();

            });
        } else {
            var sequelize = require('sequelize');
            sql = new sequelize(null, null, null, {
                storage: initdata.config.db.path,
                dialect: 'sqlite',
                logging: function(data) {
                    dblog.trace(data);
                }
            })

            models = new Models.Models(sql, "sqlite");
            log.info("Sequelize database initialized.")
            callback();
        }
    }

    init = (initdata : InitData, callback: (err,res) => void) : void =>
    {
        async.series([
                    function (cb) {initdata.prepareLogs(initdata, cb)},
                    function (cb) {initdata.loadVersion(initdata, cb)},
                    function (cb) {initdata.connectDB(initdata, cb)}, // DB init
                    function (err, res)
                    {
                        callback(null, initdata);
                    }
                ]);
    }

    constructor(args: string[]) {
        if (args.length < 1)
        {
            this.config = require('/etc/chezbob.json'); // DB config
        }
        else
        {
            this.config = require(args[0]);
        }
        this.timeout = 1000;
        this.dbname = this.config.db.name; //
        this.dbuser = this.config.db.user; // DB construction
        this.dbhost = this.config.db.host; //
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

        // drive the fpreader asyncronously
        var break_time = 1; // milliseconds
        function DRIVE_MONKEY_DRIVE() {
            server.reader.handle_eventsAsync().then();
            setTimeout( DRIVE_MONKEY_DRIVE, break_time );
        } // the astute reader will note the reference to the classic "Grandma's Boy"

                // ****** TODO read in the fingerprint data, make a list of uids, fpdatas

        // TODO race condition....
        var uid_list;
        var fpdata_list;   
        function reload_fp() {     
            models.Fingerprints.findAll({}).then( function (resu) 
                {
                    uid_list = [];
                    fpdata_list = [];
                    var resuLength = resu.length;
                    for (var i = 0; i < resuLength; i++) {
                        uid_list.push(resu[i].userid);

                        // log.info("out of db: " + resu[i].fpdata.toString('hex'));
                        // log.info("len out: " + resu[i].fpdata.length);
                        // log.info("type out: " + Object.prototype.toString.call(resu[i].fpdata));

                        fpdata_list.push(resu[i].fpdata.toString('utf8'));
              
                    }

                    log.info("array type out " + Object.prototype.toString.call(fpdata_list));

                    server.reader.update_database(fpdata_list); //.catch(function (err) {log.info("Reload fp database failed, e = " + err);} );
                }
            )
        }
        reload_fp();

        var jserver = jayson.server(
                {
                    // Upon receiving fp.enroll, start enrolling a fingerprint
                    "fp.enroll" : function (uid, callback)
                    {
                        log.info("BEGIN: Fingerprint enroll for uid " + uid);
                        // start the reader enrolling
                        server.reader.start_enrollAsync().then(
                                function (result)
                                {
                                    log.info("SUCCESS: Fingerprint enroll for uid " + uid);

                                    // enrolled FP data 
                                    var newFPdata = result[1];
                                    var newFPimg = result[2];

                                    // log.info("in to DB: " + newFPdata.toString('hex'));
                                    // log.info("len in: " + newFPdata.length);

                                    /**** TODO store the fingerprint with user uid in BOTh list and database ****/

                                    // update database (TODO handle errors)
                                    models.Fingerprints.find( { where : { userid: uid }})
                                        .then( function (res) {
                                            if (res === null) {
                                                // add a new entry to the fingerprint table
                                                return models.Fingerprints.create(
                                                {
                                                    userid: uid,
                                                    fpdata: newFPdata,
                                                    fpimg: newFPimg
                                                }).then(function (updated_fp)
                                                    {
                                                        log.info("Created fingerprint for user " + uid);
                                                        reload_fp();
                                                    })
                                            } else {
                                                // update the current user's fingerprint information
                                                return res.updateAttributes(
                                                {
                                                    fpdata : newFPdata,
                                                    fpimg : newFPimg
                                                }).then(function (updated_fp)
                                                    {
                                                        log.info("Updated fingerprint for user " + uid);
                                                        reload_fp();
                                                    })
                                            }
                                            //reload_fp();
                                        })

                                    // send image back to soda server for display
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
                                    var error = {code: 404, message: err};
                                    log.error("FAILED: Fingerprint enroll for uid " + uid + " failed, reason= " + err);
                                    callback(error, null);
                                })
                    },
                    // Upon receiving fp.stopenroll, stop whatever enrollment may be occuring
                    "fp.stopenroll" : function (uid, callback)
                    {
                        log.info("BEGIN: Stop fingerprint enroll for uid " + uid);
                        // stop the reader enrolling
                        server.reader.stop_enrollAsync().then(
                                function (result)
                                {
                                    var jresult = {
                                        success : true
                                    }
                                    log.info("SUCCESS: Stop fingerprint enroll for uid " + uid);
                                    callback(null, jresult);
                                }
                            )
                            .catch(function (err)
                                {
                                    var error = {code: 404, message: err};
                                    log.info("FAILED: Failure to stop fingerprint enroll for uid " + uid + ", reason = " + err);
                                    callback(error, null);
                                })
                    },
                    // TODO
                    "fp.identify" : function (callback)
                    {
                        log.info("BEGIN: Fingerprint identification");
                        // start the reader enrolling
                        server.reader.start_identifyAsync().then( // TODO pass in the list
                                function (result)
                                {
                                    log.info("SUCCESS: Fingerprint identification: " + result[1] +","+ uid_list[result[1]]);

                                    /**** TODO get the userid of the user at index result[1] */
                                    var matched_userid = uid_list[result[1]];
                                    //var matched_userid = 0;

                                    // send image back to soda server for display
                                    // also send the userid back to be logged in!!
                                    var jresult = {

                                        // userid to log in
                                        fpuserid : matched_userid,
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
                                    var error = {code: 404, message: err};
                                    log.error("FAILED: Fingerprint identification failed, reason= " + err);
                                    callback(error, null);
                                })
                    },
                    // Stop identification
                    "fp.stopidentify" : function (callback)
                    {
                        log.info("BEGIN: Stop fingerprint identification");
                        // stop the reader enrolling
                        server.reader.stop_identifyAsync().then(
                                function (result)
                                {
                                    var jresult = {
                                        success : true
                                    }
                                    log.info("SUCCESS: Stop fingerprint identify");
                                    callback(null, jresult);
                                }
                            )
                            .catch(function (err)
                                {
                                    var error = {code: 404, message: err};
                                    log.info("FAILED: Failure to stop fingerprint identify, reason = " + err);
                                    callback(error, null);
                                })
                    }
                }
                )
            jserver.http().listen(server.initdata.rpc_port); // start the server up

            // Constantly call the reader's event handler
            DRIVE_MONKEY_DRIVE();
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
