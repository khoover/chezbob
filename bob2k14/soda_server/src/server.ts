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
var bodyparser = require('body-parser');
var bunyanredis = require('bunyan-redis');
var io = require('socket.io');
var promise = require('bluebird');
var rpc = require('socket.io-rpc');
var sequelize = require('sequelize');
var config = require('/etc/chezbob.json');
var pgpass = require('pgpass');
var Models = require('./models');
var crypt = require('crypt3');
var redis = promise.promisifyAll(require('redis'));
var nodemailer = promise.promisifyAll(require('nodemailer'));
var ansihtml = require('ansi-to-html');
var child_process= require("child_process");
var S = require('string');
var stripansi = require('strip-ansi');

var log;
var dblog;
var ringbuffer;
var redistransport;
var sql;
var models;
var redisclient;
var mailtransport;

class InitData {
    version: String;
    longVersion: String;

    timeout: Number;

    dbname;
    dbuser;
    dbhost;

    cbemail;
    sodamap;

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
                            dblog.trace(data);
                        }
                    })
                    models = new Models.Models(sql);
                    log.info("Sequelize database initialized.")
                    callback();

        });
    }

    initSessions (initdata: InitData, callback: () => void) : void
    {
        redisclient = redis.createClient();
        callback();
    }

    initMailTransporter (initdata: InitData, callback: () => void) : void
    {
        mailtransport = promise.promisifyAll(
                nodemailer.createTransport(
                {
                    host: 'localhost',
                    port: 25,
                    ignoreTLS: true
                }
            ))
        log.info("Mail transport configured.");
        callback();
    }

    init = (initdata : InitData, callback: (err,res) => void) : void =>
    {
        async.series([
                    function (cb) {initdata.prepareLogs(initdata, cb)},
                    function (cb) {initdata.loadVersion(initdata, cb)},
                    function (cb) {initdata.connectDB(initdata, cb)},
                    function (cb) {initdata.initSessions(initdata, cb)},
                    function (cb) {initdata.initMailTransporter(initdata, cb)},
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
        this.cbemail = "chezbob@cs.ucsd.edu";

        //TODO: this needs to be read from the main config file
        this.sodamap = {
            "01" : "782740",
            "02" : "496340",
            "03" : "",
            "04" : "049000042566",
            "05" : "120130",
            "06" : "120500",
            "07" : "783150",
            "08" : "783230",
            "09" : "120850",
            "0A" : "496580"
        }
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
    clientidmap;

    iochannel;

    // balance_transfer : transfer balances from one user to another
    balance_transfer (server: sodad_server, client: string, targetuser:string,
             amt: string)
    {
        redisclient.hget("sodads:" + client, "uid", function (err,uid)
        {
            if (err)
            {
                log.error("Error retrieving for balance transfer on client " + client);
            }
            else
            {
                log.trace("Session resolved to uid " + uid + " on client " + client);
                sql.transaction(function (t)
                {
                    return models.Users.find({ where: { userid: uid }},{ transaction: t })
                        .then(function (user)
                            {
                                if (user)
                                {
                                    log.trace("User found in transaction");
                                    if (parseFloat(user.balance) < parseFloat(amt))
                                    {
                                        throw "Insufficient balance for balance transfer!"
                                    }
                                    if (parseFloat(amt) < 0)
                                    {
                                        throw "Balance transfer must be positive!"
                                    }
                                    return user.updateAttributes(
                                        {
                                            balance: (parseFloat(user.balance) - parseFloat(amt))
                                        }, { transaction: t }
                                        );
                                }
                                throw "User " + uid + " not found!"
                            })
                        .then(function (user_updated)
                            {
                                //add the transaction
                                log.trace("User updated in transaction");
                                return models.Users.find({ where: { username: targetuser}}, { transaction: t })
                                    .then(function(target_found)
                                    {
                                        if (target_found)
                                        {
                                            log.trace("Target user found in transaction");
                                            if (target_found.disabled)
                                            {
                                                throw "Cannot transfer to disabled user!"
                                            }
                                            return target_found.updateAttributes(
                                                {
                                                    balance: (parseFloat(target_found.balance) + parseFloat(amt)),
                                                }, { transaction: t })
                                            .then(function(target_updated)
                                            {
                                                return models.Transactions.create(
                                                {
                                                    userid: uid,
                                                    xactvalue: - amt,
                                                    xacttype: "TRANSFER TO " + target_updated.username,
                                                    barcode: null,
                                                    source: 'bob2k14.2',
                                                    finance_trans_id: null
                                                }, { transaction: t } )
                                            })
                                            .then(function(user_xact)
                                            {
                                                return models.Transactions.create(
                                                {
                                                    userid: target_found.userid,
                                                    xactvalue: amt,
                                                    xacttype: "TRANSFER FROM " + user_updated.username,
                                                    barcode: null,
                                                    source: 'bob2k14.2',
                                                    finance_trans_id: null
                                                }, { transaction: t } )
                                            })
                                            .then(function (target_xact)
                                            {
                                                return t.commit().then(function ()
                                                {
                                                    log.info("Balance transfer transactions successfully inserted for user " + uid + " to " + targetuser + ", client " + client);
                                                    server.clientchannels[client].addpurchase({
                                                        name: "Transfer to " + targetuser,
                                                        amount: "-" + amt,
                                                        newbalance: user_updated.balance
                                                    })
                                                });
                                            });
                                        }
                                        throw "Target user " + targetuser + " not found!"
                                    })
                             })
                        .catch(function (err)
                            {
                                log.error("Error committing transfer transaction for client " + client + ", rolling back: ", err);
                                t.rollback().then(function()
                                    {
                                        server.clientchannels[client].displayerror("fa-warning", "Transfer Error", err);
                                    }
                                    );
                            });
                });
            }
        });
    }

    // balance_transaction : generate a new balance transaction for a user.
    balance_transaction (server: sodad_server, client: string, type: string,
            purchase_description: string, barcode: string, amt: string)
    {
        redisclient.hget("sodads:" + client, "uid", function (err,uid)
        {
            if (err)
            {
                log.error("Error retrieving for balance transaction on client " + client);
            }
            else
            {
                log.trace("Session resolved to uid " + uid + " on client " + client);
                sql.transaction(function (t)
                {
                    return models.Users.find({ where: { userid: uid }},{ transaction: t })
                        .then(function (user)
                            {
                                if (user)
                                {
                                    log.trace("User found in transaction");
                                    return user.updateAttributes(
                                        {
                                            balance: (parseFloat(user.balance) + parseFloat(amt))
                                        }, { transaction: t }
                                        );
                                }
                                throw "User " + uid + " not found!"
                            })
                        .then(function (user_updated)
                            {
                                //add the transaction
                                log.trace("User updated in transaction");
                                return models.Transactions.create(
                                {
                                    userid: uid,
                                    xactvalue: + amt,
                                    xacttype: type,
                                    barcode: barcode,
                                    source: 'bob2k14.2',
                                    finance_trans_id: null
                                }, { transaction: t } )
                                .then(function (new_xact)
                                {
                                    return t.commit().then(function ()
                                    {
                                        log.info("New balance transaction successfully inserted for user " + uid + ", client " + client);
                                        server.clientchannels[client].addpurchase({
                                            name: purchase_description,
                                            amount: amt,
                                            newbalance: user_updated.balance
                                        })
                                    });
                                });
                             })
                        .catch(function (err)
                            {
                                log.error("Error committing transaction for client " + client + ", rolling back: ", err);
                                t.rollback().then(function ()
                                    {
                                         server.clientchannels[client].displayerror("fa-warning", "Transaction Error", err);
                                    })
                            });
                });
            }
        });
    }

    // transaction_history : get paginated transaction history for user.
    transaction_history (server: sodad_server, client: string, index: number,
            items: number)
    {
        return redisclient.hgetAsync("sodads:" + client, "uid")
                          .then(function (uid)
                                  {
                                    if (uid == null)
                                    { throw "User could not be found from session."; }
                                    return models.Transactions.findAndCountAll({
                                    where: { userid : uid },
                                    order: 'xacttime DESC',
                                    offset: index,
                                    limit: items
                                    })
                                  })
                          .catch(function (e)
                                  {
                                    log.error("Couldn't fetch transaction history " + e);
                                  })
    }

    handle_barcode (server: sodad_server, type: ClientType, num: number, bc_type: string, barcode: string)
    {
        var sessionid;
        if (server.clientmap[type][num] !== undefined )
        {
            sessionid = server.clientidmap[type][num];
            log.trace("Mapping session for " + ClientType[type] + "/" + num + " to " +  server.clientidmap[type][num]);
            redisclient.hgetallAsync("sodads:" + sessionid)
                .then(function (session)
                        {
                            if (session == null)
                            {
                                //nobody is logged in
                               return models.Userbarcodes.find( { where: { barcode : barcode }})
                                .then(function(userbarcode)
                                    {
                                        if (userbarcode !== null)
                                        {
                                            return models.Users.find( { where: { userid : userbarcode.userid }})
                                                .then( function (user)
                                                    {
                                                        server.handle_login(server, sessionid, "barcode", user);
                                                    })
                                        }
                                        else
                                        {
                                            //maybe it's a product? price check.
                                            return models.Products.find( { where: { barcode: barcode }})
                                                .then( function (products)
                                                {
                                                    if (products !== null)
                                                    {
                                                        log.trace("Display price for product " + products.name + " due to barcode scan.");
                                                        server.clientchannels[sessionid].displayerror("fa-barcode", "Price Check", products.name + " costs " + products.price);
                                                    }
                                                    else
                                                    {
                                                        //no idea what this is.
                                                       log.trace("Unknown barcode " + barcode + ", rejecting.")
                                                       server.clientchannels[sessionid].displayerror("fa-warning", "Unknown Barcode", "Unknown barcode " + barcode + ", please scan again.");
                                                    }
                                                });
                                        }
                                    })
                            }
                            else
                            {
                                if (session.learn === "true")
                                {
                                    //we are trying to learn this barcode
                                    log.trace("Learning mode on, add learned barcode.")
                                    models.Userbarcodes.find(
                                                {
                                                    where : {
                                                    barcode: barcode,
                                                    userid: session.uid}
                                                }
                                            ).then(function (exist_barcode) {
                                                if (exist_barcode !== null)
                                                {
                                                    throw "Barcode already learned!"
                                                }
                                                return models.Userbarcodes.create(
                                                    {
                                                        barcode: barcode,
                                                        userid: session.uid
                                                    }
                                                ).then(function (a)
                                                    {
                                                        log.info("Barcode " + barcode + " learned for client " + sessionid);
                                                        server.clientchannels[sessionid].displayerror("fa-barcode", "Barcode learned", "Barcode " + barcode + " learned");
                                                        server.clientchannels[sessionid].updatebarcodes();
                                                    })
                                            })
                                            .catch(function (e)
                                                {
                                                    log.info("Barcode " + barcode + " NOT learned for client " + sessionid + " due to error: " + e);
                                                    server.clientchannels[sessionid].displayerror("fa-warning", "Learn failed", "Barcode " + barcode + " already learned by you or another user.");
                                                })
                                }
                                else if (session.detail)
                                {
                                    //trying to get detailed info about this barcode
                                }
                                //default to purchase
                                else
                                {
                                    return models.Products.find( { where: { barcode: barcode }})
                                                .then( function (products)
                                                {
                                                    if (products !== null)
                                                    {
                                                        log.info("Purchase " + products.name + " using barcode scan.");
                                                        return models.Users.find( { where: { userid : session.uid }})
                                                            .then( function (user)
                                                            {
                                                                var purchase_desc = user.pref_forget_which_product === "true" ? "BUY" : "BUY " + products.name;
                                                                var purchase_barcode = user.pref_forget_which_product  === "true" ? null : products.barcode;
                                                                server.balance_transaction(server, sessionid, purchase_desc,
                                                                 products.name, purchase_barcode,  "-" + products.price);
                                                            })
                                                    }
                                                    else
                                                    {
                                                        //no idea what this is.
                                                       log.trace("Unknown barcode " + barcode + ", rejecting.")
                                                       server.clientchannels[sessionid].displayerror("fa-warning", "Unknown Barcode", "Unknown barcode " + barcode + ", please scan again.");
                                                    }
                                                });

                                }
                            }
                        })
        }
    }

    //getbarcode: return a list of barcodes registered to the user.
    get_barcodes( server: sodad_server, client: string )
    {
        return redisclient.hgetAsync("sodads:" + client, "uid")
                          .then(function (uid)
                                  {
                                    return models.Userbarcodes.findAll( { where : { userid: uid }})
                                  })
    }

    //forget_barcode: forgets a barcode registered to the user.
    forget_barcode( server: sodad_server, client: string, barcode: string )
    {
        return redisclient.hgetAsync("sodads:" + client, "uid")
                          .then(function (uid)
                                  {
                                    return models.Userbarcodes.find( { where : { userid: uid, barcode: barcode }})
                                        .then(function(result){
                                            if (result === null) {throw "Barcode not registered to user!"}
                                            result.destroy().then(function (deleted)
                                                {
                                                    server.clientchannels[client].displayerror("fa-trash", "Barcode deleted", "Barcode " + barcode + " deleted");
                                                    server.clientchannels[client].updatebarcodes();
                                                })
                                        })
                                  })
    }

    learnmode_barcode( server: sodad_server, client: string, learnmode: boolean)
    {
        return redisclient.hsetAsync("sodads:" + client, "learn", learnmode);
    }

    updateuser(server: sodad_server, client: string)
    {
        return redisclient.hgetAsync("sodads:" + client, "uid")
                          .then(function (uid)
                                  {
                                    return models.Users.find( { where : { userid: uid }})
                                        .then(function(result){
                                                var user = result;
                                                user.pwd = (user.pwd === null || user.pwd === '') ? false: true;
                                                server.clientchannels[client].updateuser(user);
                                            })
                                  });
    }

    changepassword (server: sodad_server, client: string, enabled: boolean,
            newpassword: string, oldpassword: string)
    {
        return redisclient.hgetAsync("sodads:" + client, "uid")
                          .then(function (uid)
                                  {
                                    return models.Users.find( { where : { userid: uid }})
                                        .then(function(result){
                                            if (result === null) {throw "Couldn't find user to change password!"}
                                            else if (!(result.pwd === null || result.pwd === ""))
                                            {
                                                if (crypt(oldpassword, "cB") !== result.pwd)
                                                {
                                                    throw "Old password is incorrect!"
                                                }
                                            }
                                            var newpass = enabled ? crypt(newpassword, "cB") : null;
                                            return result.updateAttributes(
                                                    {
                                                        pwd : newpass
                                                    }).then(function (updated_user)
                                                        {
                                                            log.info("Successfully updated password for user " + updated_user.username + " on client "  + client);
                                                            server.clientchannels[client].displayerror("fa-check", "Update success", "Password settings updated");
                                                            server.updateuser(server, client);
                                                        })
                                            })
                                  })
                        .catch(function (e)
                                {
                                    log.info("Failed to update password due to " + e);
                                    server.clientchannels[client].displayerror("fa-close", "Update failure", "Couldn't update passwords: " + e);
                                })
    }

    //maybe make this a library function
    debunyanize (log: string[], callback: (Object, string) => void)
    {
        var bunyanproc = child_process.spawn('bunyan', ["--color"]);
        bunyanproc.stdout.setEncoding('utf8');
        var bunyanstr = '';
        bunyanproc.stdout.on('data', function(data) {
            bunyanstr += data;
        })
        bunyanproc.stdout.on('close', function(code){
            return callback(null, bunyanstr);
        });
        log.forEach(function (item)
                {
                    var unescaped = S(item).replaceAll('\n', '')
                    bunyanproc.stdin.write(unescaped + "\n");
                })

        //this should close bunyan
        bunyanproc.stdin.end("\x04");
    }
    //maybe this should create a github issue?
    bug_report (server: sodad_server, client: string, report: string)
    {
        return redisclient.hgetallAsync("sodads:" + client)
            .then(function(udata)
                {
                    log.info("User " + udata.username + " submitted a bug report, collecting log.");
                    //collect log.
                    return redisclient.lrangeAsync("cb_log", 0, -1).then(
                        function (lrange)
                        {
                            var debunyanizeAsync = promise.promisify(server.debunyanize, server);
                            return debunyanizeAsync(lrange.slice(0,200)).then(function(ansilog)
                            {
                                var converter = new ansihtml(
                                    {
                                        newline: true,
                                        escapeXML: true,
                                        bg: '#fff',
                                        fg: '#000'
                                    }
                                    );
                                //lrange is an array of log entries.
                                var mailOpts = {
                                    from: server.initdata.cbemail,
                                    to: server.initdata.cbemail,
                                    cc: udata.email,
                                    subject: '[cb_bugreport] Bug report from ' + udata.username,
                                    html: 'User ' + udata.username + " submitted a bug report:<br/><br/>" + report + '<br/><br/> The json log corresponding to this report is attached, and the first 200 log entries follow:<br/<br/>' + converter.toHtml(ansilog),
                                    text: 'User ' + udata.username + " submitted a bug report:\n\n" + report + '\n\n The json log corresponding to this report is attached, and the first 200 log entries follows:\n\n' + stripansi(ansilog),
                                    attachments: [
                                        {
                                            filename: 'log.json',
                                            content: lrange.join('\n')
                                        }
                                    ]
                                };
                                return mailtransport.sendMailAsync(mailOpts).then(function (response)
                                    {
                                        log.info("Bug report successfully e-mailed for user " + udata.username);
                                        server.clientchannels[client].displayerror("fa-check", "Report Submitted", "Thanks for your report! We'll get to squashing this bug soon.");
                                    })
                            })
                        }
                        )
                }
            )
            .catch(function(e)
                    {
                        log.error("Error sending bug report: " + e);
                        server.clientchannels[client].displayerror("fa-close", "Well this is embarassing...", "Could not submit your report - please e-mail chezbob@cs.ucsd.edu. Error: " + e);
                    })
    }

    issue_report (server: sodad_server, client: string, report: string)
    {
        return redisclient.hgetallAsync("sodads:" + client)
            .then(function(udata)
                {
                    log.info("User " + udata.username + " submitted an issue report");
                    var mailOpts = {
                        from: server.initdata.cbemail,
                        to: server.initdata.cbemail,
                        cc: udata.email,
                        subject: '[cb_issuereport] Account issue report from ' + udata.username,
                        html: 'User ' + udata.username + " submitted an issue report:<br/><br/>" + report,
                        text: 'User ' + udata.username + " submitted an issue report:\n\n" + report,
                    };
                    return mailtransport.sendMailAsync(mailOpts).then(function (response)
                        {
                            log.info("Issue report successfully e-mailed for user " + udata.username);
                            server.clientchannels[client].displayerror("fa-check", "Report Submitted", "Thanks for your report! We'll get back to you about your accounts soon.");
                        })
                })
            .catch(function(e)
                    {
                        log.error("Error sending issue report: " + e);
                        server.clientchannels[client].displayerror("fa-close", "Well this is embarassing...", "Could not submit your report - please e-mail chezbob@cs.ucsd.edu. Error: " + e);
                    })
    }

    oos_report (server: sodad_server, client: string, barcode: string)
    {
        return redisclient.hgetallAsync("sodads:" + client)
            .then(function(udata)
                {
                    log.info("User " + udata.username + " submitted an oos report");
                    return models.Products.find({where: {barcode : String(barcode)}}).then(function (product) {
                        var mailOpts = {
                            from: server.initdata.cbemail,
                            to: server.initdata.cbemail,
                            cc: udata.email,
                            subject: '[cb_oos] OOS of ' + product.name,
                            html: 'User ' + udata.username + " submitted an oos report for " + product.name + ", barcode " + product.barcode,
                            text: 'User ' + udata.username + " submitted an oos report for " + product.name + ", barcode " + product.barcode,
                        };
                        return mailtransport.sendMailAsync(mailOpts).then(function (response)
                            {
                                log.info("OOS report successfully e-mailed for user " + udata.username);
                                server.clientchannels[client].displayerror("fa-check", "Report Submitted", "Thanks for your report! Hopefully a restocker will get you more " + product.name + " soon.");
                            })
                    });
                })
            .catch(function(e)
                    {
                        log.error("Error sending oos report: " + e);
                        server.clientchannels[client].displayerror("fa-close", "Well this is embarassing...", "Could not submit your report - please e-mail chezbob@cs.ucsd.edu. Error: " + e);
                    })
    }

    //btw anonymous seems pretty silly since we can figure out who sent via logs???
    comment_report (server: sodad_server, client: string, report: string, anonymous: boolean)
    {
        return redisclient.hgetallAsync("sodads:" + client)
            .then(function(udata)
                {
                    if (!anonymous)
                    {
                        log.info("User " + udata.username + " submitted a comment report");
                    }
                    var cc = anonymous ? null : udata.email;
                    var subject = anonymous ? "[cb_comment] Comment from anonymous" : "[cb_comment] Comment from " + udata.username;
                    var mailOpts = {
                        from: server.initdata.cbemail,
                        to: server.initdata.cbemail,
                        cc: cc,
                        subject: subject,
                        html: 'User submitted an comment report:<br/><br/>' + report,
                        text: 'User submitted an comment report:\n\n' + report
                    };
                    return mailtransport.sendMailAsync(mailOpts).then(function (response)
                        {
                            if (!anonymous)
                            {
                                log.info("Comment report successfully e-mailed for user " + udata.username);
                            }
                            server.clientchannels[client].displayerror("fa-check", "Report Submitted", "Thanks for your comment! We'll look into this as resources permit.");
                        })
                })
            .catch(function(e)
                    {
                        log.error("Error sending comment report: " + e);
                        server.clientchannels[client].displayerror("fa-close", "Well this is embarassing...", "Could not submit your report - please e-mail chezbob@cs.ucsd.edu. Error: " + e);
                    })
    }

    handle_login (server: sodad_server, client: string, source: string, user)
    {
            var multi = redisclient.multi();
            multi.hset("sodads:" + client, "uid", user.userid); //TODO: deprecated key uid
            multi.hmset("sodads:" + client, user)
            multi.expire("sodads:" + client, 600);
            multi.exec();
            log.info("Successfully authenticated " + user.username +
                " (" + source + ") for client " + client);
            if (user.pwd !== null && user.pwd !== '')
            {
                user.pwd = true;
            }
            else
            {
                user.pwd = false;
            }
            server.clientchannels[client].login(user);
    }

    oos_search (server: sodad_server, client: string, searchstring: string)
    {
        return models.Products.findAll(
                {
                    where: [ "name ILIKE '" + searchstring +"%'" ],
                    limit: 5
                }
                ).then(function (products)
                    {
                        return products;
                    }
                    )
    }
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

        var jsonserver = jayson.server({
            "Soda.remotebarcode" : function (type, barcode, cb)
            {
                log.trace("Got remote barcode "  + barcode);
                server.handle_barcode(server, ClientType.Soda, 0, type, barcode);
                cb(null);
            },
            "Soda.vdbauth" : function (requested_soda, cb)
            {
                var sessionid;

                //for now, there is only one client attached to the soda machine.
                var type:ClientType = ClientType.Soda;
                var num: number = 0;
                if (server.clientmap[type][num] !== undefined )
                {
                    sessionid = server.clientidmap[type][num];
                    log.trace("Mapping session for " + ClientType[type] + "/" + num + " to " +  server.clientidmap[type][num]);
                    redisclient.hgetallAsync("sodads:" + sessionid)
                        .then (function (session)
                            {
                                if (session === null)
                                {
                                    log.info ("Vend request for " + requested_soda + " DENIED due to no session");
                                    server.clientchannels[sessionid].displayerror("fa-warn", "Vend DENIED", "You must be logged in to buy soda.");
                                    cb(null, false);
                                }
                                else
                                {
                                    log.info("Vend request for " + requested_soda + " AUTHORIZED for user " + session.username);
                                    //get requested soda name...
                                    models.Products.find({where : {barcode : server.initdata.sodamap[requested_soda] }})
                                        .then(function (sodainfo)
                                            {
                                                server.clientchannels[sessionid].displaysoda(requested_soda, sodainfo.name);
                                                redisclient.hsetAsync("sodads:" + sessionid, "activevend", true).then(function ()
                                                {
                                                    cb(null, true);
                                                });
                                            });
                                }
                            }).catch(function (e)
                                {
                                    log.error("Vend request for " + requested_soda + " DENIED due to lookup error " + e);
                                    server.clientchannels[sessionid].displayerror("fa-warning", "Vend DENIED", "Lookup error " + e);
                                    cb(null, false);
                                })
                }
                else
                {
                    log.info("Vend request for " + requested_soda + " DENIED due to no session or socket");
                    cb(null, false); //DENY vend, no one is logged in (and the browser isn't even pointed at this page)
                }
            },
            "Soda.vdbvend" : function (success, requested_soda, cb)
            {
                log.info("Vend result is " + success);
                var sessionid;

                //for now, there is only one client attached to the soda machine.
                var type:ClientType = ClientType.Soda;
                var num: number = 0;
                if (server.clientmap[type][num] !== undefined )
                {
                    sessionid = server.clientidmap[type][num];
                    log.trace("Mapping session for " + ClientType[type] + "/" + num + " to " +  server.clientidmap[type][num]);
                    redisclient.hgetallAsync("sodads:" + sessionid)
                        .then (function (session)
                            {
                                if (session === null)
                                {
                                    log.error("Vend result=" + success + " for " + requested_soda + " NOT RECORDED due to no session!");
                                    cb(null);
                                }
                                else
                                {
                                        log.info("Vend result=" + success + " for " + requested_soda + " recorded for " + session.username);
                                        redisclient.hsetAsync("sodads:" + sessionid, "activevend", false).then(function ()
                                                    {
                                                        if (success)
                                                        {
                                                        models.Products.find({where : {barcode : server.initdata.sodamap[requested_soda] }})
                                                            .then(function (sodainfo)
                                                            {
                                                                log.info("Purchase " + sodainfo.name + " due to soda vend");
                                                                var purchase_desc = session.pref_forget_which_product === "true" ? "BUY" : "BUY " + sodainfo.name;
                                                                var purchase_barcode = session.pref_forget_which_product === " true" ? null : sodainfo.barcode;
                                                                server.balance_transaction(server, sessionid, purchase_desc,
                                                                 sodainfo.name, purchase_barcode,  "-" + sodainfo.price);
                                                                cb(null);
                                                            })
                                                        }
                                                        else
                                                        {
                                                            log.info("Notifying client and recoding OOS for " + requested_soda);
                                                            server.clientchannels[sessionid].displayerror("fa-warning", "Sold Out", "Sorry, looks like we are sold out. Don't worry, you won't be charged.");
                                                            cb(null);
                                                        }
                                                    });
                                }
                            }).catch(function (e)
                                {
                                    log.error("Vend result=" + success + " for " + requested_soda + " NOT RECORDED due to " + e);
                                    server.clientchannels[sessionid].displayerror("fa-warn", "Vend ERROR", "Lookup error " + e);
                                    cb(null, false);
                                })
                }
                else
                {
                    log.error("Vend result=" + success + " for " + requested_soda + " NOT RECORDED due to no session!");
                    cb(null);
                }

            }
        });

        this.app.use('/api', bodyparser.json());
        this.app.use('/api', jsonserver.middleware());
        this.server = this.app.listen(config.sodad.port, function() {

        });

        this.clientchannels = {};
        this.clientmap = {};
        this.clientmap[ClientType.Terminal] = {};
        this.clientmap[ClientType.Soda] = {};
        this.clientidmap = {};
        this.clientidmap[ClientType.Terminal] = {};
        this.clientidmap[ClientType.Soda] = {};

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
                var client = this.id;
                return redisclient.hgetAsync("sodads:" + client, "activevend")
                    .then(function(activevend)
                            {
                                if (activevend === "true")
                                {
                                    log.warn("Logout cancelled due to active vending session");
                                    throw "Active vending session prevents logout!";
                                }
                                else
                                {
                                    return redisclient.delAsync("sodads:" + client)
                                                      .then(function()
                                                          {
                                                            log.info("Logging out session for client " + client);
                                                            server.clientchannels[client].logout();
                                                          })
                                }
                            })
            },
            manualpurchase: function(amt)
            {
                var client = this.id;
                log.info("Manual purchase of " + amt + " for client " + client);
                server.balance_transaction(server, client, "BUY OTHER",
                        "Manual Purchase", null, "-" + amt);
            },
            manualdeposit: function(amt)
            {
                var client = this.id;
                log.info("Manual deposit of " + amt + " for client " + client);
                server.balance_transaction(server, client, "ADD MANUAL",
                        "Manual Deposit", null,  amt);
            },
            transfer: function(amt, user)
            {
                var client = this.id;
                log.info("Balance transfer of " + amt + " to " + user + " for client " + client);
                server.balance_transfer(server, client, user, amt);
            },
            transactionhistory: function(index, count)
            {
                var client = this.id;
                log.info("Transaction history request for index " + index + ", count " + count + " for client " + client);
                return server.transaction_history(server, client, index, count);
            },
            get_barcodes: function()
            {
                var client = this.id;
                log.info("Getting barcodes registered for client " + client);
                return server.get_barcodes(server, client);
            },
            forget_barcode: function(barcode)
            {
                var client = this.id;
                log.info("Forget barcode requested for client "  + client);
                return server.forget_barcode(server, client, barcode);
            },
            learnmode_barcode: function(mode)
            {
                var client = this.id;
                log.info("Setting learn mode to " + mode  + " for client " + client);
                return server.learnmode_barcode(server, client, mode);
            },
            bug_report: function(report)
            {
                var client = this.id;
                log.info("Submitting a bug report for client " + client);
                return server.bug_report(server, client, report);
            },
            issue_report: function(report)
            {
                var client = this.id;
                log.info("Submitting an issue report for client " + client);
                return server.issue_report(server, client, report);
            },
            comment_report: function(anonymous, report)
            {
                var client = this.id;
                log.info("Submitting an comment report for client " + client);
                return server.comment_report(server, client, report, anonymous);
            },
            changepassword: function(enable, newpassword, oldpassword)
            {
                var client = this.id;
                log.info("Setting password (enabled=" + enable + ") for client " + client);
                return server.changepassword(server, client, enable, newpassword, oldpassword);
            },
            oos_search: function(searchphrase)
            {
                var client = this.id;
                log.info("Executing OOS search for " + searchphrase + " for client " + client);
                return server.oos_search(server, client, searchphrase);
            },
            oos_report: function(barcode)
            {
                var client = this.id;
                log.info("Submitting an OOS report for barcode " + barcode + " for client " + client);
                return server.oos_report(server, client, barcode);
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
                                else if (entry == null) {
                                    log.warn("Couldn't find user " + user + " for client " + client);
                                    server.clientchannels[client].displayerror("fa-warning", "User not found", "Login for account " + user + " not found.");
                                }
                                else
                                {
                                    var luser = entry.dataValues;
                                    if (luser.disabled)
                                    {
                                        log.warn("Disabled user " + user + " attempted login from client " + client);
                                        server.clientchannels[client].displayerror("fa-times-circle", "Login Disabled", "Login for account " + user + " is disabled. Please contact ChezBob staff for more details.");
                                    }
                                    else if (luser.pwd == null && password == "")
                                    {
                                        server.handle_login(server, client, "no pass", luser);
                                    }
                                    else
                                    {
                                        if(crypt(password, "cB") === luser.pwd)
                                        {
                                            server.handle_login(server, client, "password", luser);
                                        }
                                        else
                                        {
                                            log.warn("Authentication failure for client " + client);
                                            server.clientchannels[client].displayerror("fa-times-circle", "Login Denied", "Login for account " + user + " denied. Incorrect password was entered.");
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
                        server.clientidmap[typedata.type][typedata.id] = socket.id;
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
