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
import Buffer = require('buffer');
import express = require('express')
var bunyanredis = require('bunyan-redis');
var io = require('socket.io');
var promise = require('bluebird');
var rpc = require('socket.io-rpc');
var sequelize = require('sequelize');
var config = require('/etc/chezbob.json');
var pgpass = require('pgpass');
var Models = require('./models');
var crypt = require('crypt3');
var redis = require('redis');

var log;
var dblog;
var ringbuffer;
var redistransport;
var sql;
var models;
var redisclient;

class InitData {
    version: String;
    longVersion: String;

    timeout: Number;

    dbname;
    dbuser;
    dbhost;

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
                );4
        log.info("Logging system initialized");
        callback();
    }

    connectDB = (initdata : InitData, callback: () => void) : void  =>
    {
        dblog = log.child({module: 'db'});
        pgpass({host: this.dbhost,
                user: this.dbuser}, function (password)
                {
                    sql = new sequelize(initdata.dbname, initdata.dbuser, password,  {
                        host: initdata.dbhost,
                        dialect: 'postgres',
                        logging: function(data) {
                            dblog.debug(data);
                        }
                    })
                    models = new Models.Models(sql);
                    log.info("Sequelize database initialized.")
                    callback();

        });
    }

    initSessions = (initdata: InitData, callback: () => void) : void =>
    {
        redisclient = redis.createClient();
        callback();
    }

    init = (initdata : InitData, callback: (err,res) => void) : void =>
    {
        async.series([
                    function (cb) {initdata.prepareLogs(initdata, cb)},
                    function (cb) {initdata.loadVersion(initdata, cb)},
                    function (cb) {initdata.connectDB(initdata, cb)},
                    function (cb) {initdata.initSessions(initdata, cb)},
                    function (err, res)
                    {
                        callback(null, initdata);
                    }
                ]);
    }

    constructor(args: string[]) {
        this.timeout = 10000;
        this.dbname = "bob";
        this.dbuser = "bob";
        this.dbhost = "localhost";
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

//TODO: this needs to be sync'd with client code
enum ClientType {
    Terminal = 0,
    Soda = 1
}

class sodad_server {
    initdata : InitData; //initialization data
    app;
    server;
    clientloggers;
    clientchannels;
    clientmap;

    iochannel;

    start = () => {
        var server = this;
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

        this.clientchannels = {};
        this.clientmap = {};
        this.clientmap[ClientType.Terminal] = {};
        this.clientmap[ClientType.Soda] = {};

        this.iochannel = io.listen(this.server);
        rpc.createServer(this.iochannel, this.app);
        rpc.expose('serverChannel',{
            log: function(level: log_level, data)
            {
                var clog = log.child({module: 'client', id: this.id});
                switch(level)
                {
                    case log_level.TRACE:
                        clog.trace(data);
                        break;
                    case log_level.DEBUG:
                        clog.debug(data);
                        break;
                    case log_level.INFO:
                        clog.info(data);
                        break;
                    case log_level.WARN:
                        clog.warn(data);
                        break;
                    case log_level.ERROR:
                        clog.error(data);
                        break;
                    case log_level.FATAL:
                        clog.fatal(data);
                }
            },
            barcodestats: function(barcode)
            {
                return models.Transactions.count( { where:  { barcode : barcode } } );
            },
            barcode: function(barcode)
            {
                var deferred = promise.defer();
                models.Products.find(barcode)
                    .complete(function(err, entry)
                            {
                                deferred.resolve(entry.dataValues);
                            })
                return deferred.promise;
            },
            logout: function()
            {
                redisclient.del("sodads:" + this.id);
                log.info("Logging out session for client " + this.id);
                server.clientchannels[this.id].logout();
                return true;
            },
            manualpurchase: function(amt)
            {
                log.info("Manual purchase of " + amt + " for client " + this.id);
                server.clientchannels[this.id].addpurchase({
                    name: 'Manual Purchase',
                    amount: amt,
                    newbalance: '5.30'
                })
            },
            authenticate: function(user, password)
            {
                var deferred = promise.defer();
                var client = this.id;
                models.Users.find(
                        {
                            where: {
                                username: user
                            }
                        })
                            .complete(function (err,entry)
                            {
                                if (err) { log.error(err); }
                                else if (entry == null) { log.warn("Couldn't find user " + user + " for client " + client);}
                                else
                                {
                                    var luser = entry.dataValues;
                                    if (luser.disabled)
                                    {
                                        log.warn("Disabled user " + user + " attempted login from client " + client);
                                    }
                                    else if (luser.pwd == null && password == "")
                                    {
                                        var multi = redisclient.multi();
                                        multi.hset("sodads:" + client, "uid", luser.id);
                                        multi.expire("sodads:" + client, 600);
                                        multi.exec();
                                        log.info("Successfully authenticated " + user +
                                            " (no pass) for client " + client);
                                        server.clientchannels[client].login(luser);
                                    }
                                    else
                                    {
                                        if(crypt(password, "cB") === luser.pwd)
                                        {
                                            var multi = redisclient.multi();
                                            multi.hset("sodads:" + client, "uid", luser.id);
                                            multi.expire("sodads:" + client, 600);
                                            multi.exec();
                                            log.info("Successfully authenticated " + user +
                                            " (password) for client " + client);
                                            server.clientchannels[client].login(luser);
                                        }
                                        else
                                        {
                                            log.warn("Authentication failure for client " + client);
                                        }
                                    }
                                }

                            deferred.resolve(true);
                            }
                            );
                return deferred.promise;
            }
        });

        this.iochannel.sockets.on('connection', function (server: sodad_server){
        return function(socket)
        {
            rpc.loadClientChannel(socket, 'clientChannel').then(function (fns)
                {
                    server.clientchannels[socket.id] = fns;
                    fns.gettype().then(function (typedata){
                        server.clientmap[typedata.type][typedata.id] = fns;
                        log.info("Registered client channel type (" + ClientType[typedata.type] + "/"
                            + typedata.id + ") for client " + socket.id);
                    });
                }
                )
        }} (this));

        this.iochannel.sockets.on('disconnect', function (server: sodad_server){
            return function(socket)
            {
                delete server.clientchannels[socket.id];
                log.info("Deregistered client channel for client " + socket.id);
            }
        })
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
