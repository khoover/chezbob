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

var InitData = (function () {
    function InitData() {
        this.prepareLogs = function (initdata, callback) {
            log = bunyan.createLogger({
                name: 'mdb-server',
                streams: [
                    {
                        stream: process.stdout,
                        level: "debug"
                    }
                ]
            });
            log.info("Logging system initialized");
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
                callback();
            };
        }(initdata));
    };
    return InitData;
})();

var app = (function () {
    function app() {
    }
    app.prototype.main = function (args) {
        this.initdata = new InitData();
        this.initdata.init(this.initdata, function (err, res) {
            log.info("Hi.");
        });
    };
    return app;
})();
exports.app = app;
