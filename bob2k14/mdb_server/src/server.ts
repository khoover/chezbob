/// <reference path="../typings/tsd.d.ts"/>

var git = require('git-rev-2');
var async = require('async');
var pkginfo = require('pkginfo')(module);
var http = require('http');
var repl = require('repl');
var stream = require('stream');
var util = require('util');
var bunyan = require('bunyan');


var log;

class InitData {
    version: String;
    longVersion: String;

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
                callback();
            }
        }(initdata))
    }

    prepareLogs = (initdata: InitData, callback: () => void) : void =>
    {
        log = bunyan.createLogger(
                {
                    name: 'mdb-server',
                    streams: [
                    {
                        stream: process.stdout,
                        level: "debug"
                    }
                    ]
                }
                );
        log.info("Logging system initialized");
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

    constructor() {

    }
}

export class app {
    private initdata : InitData;

    main(args: Object[])
    {
        this.initdata = new InitData();
        this.initdata.init(this.initdata,
                function (err, res: InitData)
                {
                    log.info("Hi.");
                }
                );
    }

    constructor () {}
}
