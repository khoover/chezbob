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

var log;
var ringbuffer;
var redistransport;

class InitData {
    version: string;
    longVersion: string;

    mdbport: string;
    timeout: Number;
    remote_endpoint: string;
    rpc_port: number;
    event_mode: boolean;
    config;

    private loadVersion: (callback: () => void) => void = (cb: () => void) =>
    {
        log.debug("Getting version information...");
        this.version = module.exports.version;
        this.longVersion = module.exports.version;
        //if we are in a git checkout, append the short SHA.
        git.short(__dirname, (err, str) =>
            {
                if (err === null)
                {
                    log.debug("Git checkout detected.");
                    this.version += "+";
                    this.longVersion += "/" + str;
                }
                log.info("mdb_server version " + this.longVersion);
                cb();
            })
    }

    private prepareLogs: (callback: () => void) => void = (cb: () => void) =>
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
                    name: 'mdb-server',
                    streams: [
                    {
                        stream: process.stdout,
                        level: "trace"
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
        cb();
    }

    init: (callback: (err,res) => void) => void = (cb: (err,res) => void) =>
    {
        async.series([
                    this.prepareLogs,
                    this.loadVersion,
                    function (err, res)
                    {
                        cb(null, initdata);
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

        this.mdbport = this.config.mdbd.device;
        this.timeout = this.config.mdbd.timeout;
        this.remote_endpoint = this.config.sodad.endpoint;
        this.rpc_port = this.config.mdbd.port;
        this.event_mode = this.config.mdbd.event_mode;
    }
}

class mdb_server {
    initdata : InitData; //initialization data

    current_buffer: string; //current data being read in
    port; // open port
    port_lock: boolean; //lock for sending data to mdb device
    port_queue: Array<() => void>; //queue of jobs waiting for the port to open
    rpc_client;

    //sends the commands to reset the mdb device
    reset (): void {
        async.series([
                // Reset the coin changer
                function (cb) { this.sendread("R1", 'Z', cb); },
                function (cb) { this.sendread("N FFFF", cb); },
                function (cb) { this.sendread("M FFFF", cb); },
                function (cb) { this.sendread("P1", cb); },
                function (cb) { this.sendread("E1", cb); },
                // Reset the bill reader
                function (cb) { this.sendread("R2", cb); },
                function (cb) { this.sendread("P2", cb); },
                function (cb) { this.sendread("L FFFF", cb); },
                function (cb) { this.sendread("V 0000", cb); },
                function (cb) { this.sendread("J FFFF", cb); },
                function (cb) { this.sendread("S7", cb); }
                //function (cb) { this.sendread("E2", cb); }
           ],
           function (error, result)
           {
               if (error === null) {
                   log.info("Coin reader and bill reader successfully reset.", result);
               } else {
                   log.error("Coin and bill reader encountered error while resetting.", error);
                   throw error;
               }
           });
    }

    //creates a callback that filters for strings starting with either a single prefix or one of a list
    //if prefix is a string, assumes callback does not expect the prefix
    //if prefix is an array, gives the matched prefix back along with the message; no prefix should match any other
    makeMessageListener (prefix: string | string[], callback: (message: string, prefix?: string) => void): (message: string) => void {
        if (typeof prefix === "string" {
            return (message) => {
                if (message.startsWith(prefix)) { callback(message) }
            };
        } else {
            return (message) => {
                var matched: string[] = prefix.filter(pre => message.startsWith(pre));
                if (matched.length === 1) {
                    callback(message, matched[0]);
                }
            };
        }
    }

    //acquire the serial port for communication
    //callback must not throw any errors
    acquirePort (callback: () => void): void {
        log.trace("acquiring port");
        if (!this.port_lock)
        {
            this.port_lock = true;
            callback();
        }
        else
        {
            this.port_queue.push(callback.bind(this));
        }
    }

    //release the serial port after communication
    releasePort (): void {
        if (this.port_queue.length === 0)
        {
            this.port_lock = false;
        }
        else
        {
            process.nextTick(this.port_queue.shift());
        }
        log.trace("released port");
    }

    //asynchronusly sends a string and returns the result in a callback
    //a timeout occurs if data is not returned within the timeout.
    sendread (data: string, prefix: string | string[], cb: (error: any, message?: string, prefix?: string) => void): void {
        var cancelled: boolean = false;
        var port_acquired: boolean = false;
        var listener_event: string;
        var listener: (message?: string) => void;

        //add a timeout for communication/acquiring the port.
        const timeout = setTimeout(() => {
            if (typeof listener !== "undefined") this.port.removeListener(listener_event, listener);
            cancelled = true;
            log.error("Serial communication timed out");
            if (port_acquired) this.releasePort();
            cb("timeout");
        }, this.initdata.timeout);

        this.acquirePort(() => {
            port_acquired = true;
            log.trace("acquired port");
            if (cancelled) return this.releasePort(); //timed out, release port now
            try
            {
                listener_event = 'ACK';
                //creates the ACK listener
                listener = () => {
                    if (!cancelled) {
                        listener_event = 'message';
                        //creates the message listener
                        listener = this.makeMessageListener(prefix, (message, prefix) => {
                            this.port.removeListener('message', listener);
                            if (!cancelled) {
                                clearTimeout(timeout);
                                this.releasePort();
                                cb(null, message, prefix);
                            }
                        });
                        //registers the listener on the port
                        this.port.on('message', listener);
                    }
                };
                //add the ACK listener before sending data; avoids case of missing the ACK
                this.port.once('ACK', listener);

                //send the data
                this.send(data, (err) => {
                    if (err && !cancelled) {
                        if (typeof listener !== "undefined") this.port.removeListener(listener_event, listener);
                        cancelled = true;
                        clearTimeout(timeout);
                        this.releasePort();
                        cb(err);
                    }
                });
            }
            catch (err) //catch any synchronous errors
            {
                log.error("Error during serial communication: ", e);
                if (!cancelled) {
                    if (typeof listener !== "undefined") this.port.removeListener(listener_event, listener);
                    cancelled = true;
                    clearTimeout(timeout);
                    this.releasePort();
                    cb(err);
                }
            }
        });
    }

    //asynchrnously sends a string over port
    send (data: string, cb = (err, results) => { }): void {
        log.debug("send: ", data);
        this.port.write(data + '\r', (err, results) => {
            if (err) {
                log.error("Error while writing to serial port: ", err);
            }
            cb(err, results);
        });
    }

    start (): void {
        log.info("mdb_server starting, listening on " + this.initdata.mdbport);
        this.port = new serialport(this.initdata.mdbport);
        this.port.on("open", () =>
                {
                    log.debug("serial port successfully opened.");
                    this.port.on('data', (data : Buffer) =>
                    {
                        //it is highly unlikely that we got more than
                        //1 byte, but if we did, make sure to process
                        //each byte
                        for (var i : number = 0; i < data.length; i++)
                        {
                            switch (data[i])
                            {
                                case 0xa:
                                    log.debug("received ACK");
                                    this.port.emit('ACK');
                                    break;
                                case 0xd:
                                    log.debug("received " + this.current_buffer);
                                    if (this.current_buffer.startsWith('X')) log.error("got an error message: ", this.current_buffer);
                                    this.port.emit('message', this.current_buffer);
                                    this.current_buffer = "";
                                    break;
                                default:
                                    this.current_buffer += data.toString('utf8', i, i+1);
                            }
                        }
                    });

                    if (this.initdata.event_mode)
                    {
                        //add listener for bill escrow messages
                        this.port.on('message', this.makeMessageListener('Q1', (message: string) => {
                        }));
                        //add listener for coin deposit messages
                        this.port.on('message', this.makeMessageListener('P1', (message: string) => {
                        });
                        //add listener for logout button
                        this.port.on('message', this.makeMessageListener('W', () => {
                        });
                    }
                    else
                    {
                        //add polling calls to the bill and change acceptors
                    }
//                            if (process_last)
//                            {
//                                if (this.last_buffer[0] != "X")
//                                {
//                                //send to the remote endpoint.
//                                this.rpc_client.request("Soda.remotethis", [this.last_buffer], function (err, response)
//                                        {
//                                            if (err)
//                                            {
//                                                log.error("Error contacting remote endpoint", err);
//                                            }
//                                            else
//                                            {
//                                                log.debug("remotethis successful, response=", response);
//                                            }
//                                        });
//                                }
//                                else
//                                {
//                                    log.trace("Error ignored: " + this.last_buffer);
//                                }
//                            }

                    this.reset();

                    var server = jayson.server(
                            {
                                "Mdb.command": jayson.Method((argobj: Object, callback) =>
                                    {
                                        var command: string = argobj.command;
                                        if (command === '') {
                                            return callback(server.error(-32602, 'Empty command given.'));
                                        }
                                        var prefixes: string = argobj.response_prefixes
                                        log.debug("remote request: " + command);
                                        if (command.includes('\r')) {
                                            return callback(server.error(-32602, 'Multiple commands in single request.'));
                                        }
                                        this.sendread(command, prefixes, (err, message) => {
                                            if (err) {
                                                if (typeof err === "string" && err === "timeout") {
                                                    callback(server.error(504, 'Serial port communication timed out.'));
                                                } else {
                                                    callback(server.error(500, 'Serial port error, see attached object.', err));
                                                }
                                            } else {
                                                callback(null, message);
                                            }
                                        });
                                }, {
                                    collect: true,
                                    params: { command: '', response_prefixes: '' }
                                }),
                                "Mdb.logs": function (callback)
                                {
                                    callback(null, ringbuffer.records);
                                }
                            }
                            )
                    server.http().listen(this.initdata.rpc_port);
                    log.info("rpc endpoint listening on port " + this.initdata.rpc_port);
                });
        this.port.on("error", function (error)
                {
                    log.error("Fatal serial port error - " + error);
                    process.exit(1);
                });
    }

    constructor(initdata : InitData) {
        this.initdata = initdata;
        this.current_buffer = "";
        this.rpc_client = jayson.client.http(initdata.remote_endpoint);
        this.port_lock = false;
        this.port_queue = [];
    }
}
export class App {
    private initdata : InitData;

    main(args: string[])
    {
        this.initdata = new InitData(args);
        this.initdata.init(function (err, res: InitData)
                {
                    var mdb = new mdb_server(res);
                    mdb.start();
                });
    }

    constructor () {}
}
