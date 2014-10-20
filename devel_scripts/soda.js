#! /usr/bin/env node
var usage = " soda --deploy <deploy dir> --db <path-to-database> --port_start [num]"
// Library Imports
var util = require("util")
var argv = require("optimist")
           .usage(usage)
           .default("port_start", 8080)
           .demand(["deploy", "db", "port_start"]).argv
var fs = require("fs")
var spawn = require("child_process").spawn
var repl = require("repl")
var path = require("path")
var serialport = require("serialport").SerialPort

// Utility functions
var fmt = util.format

function die() {
  if (arguments.length > 0) {
    log(fmt.apply(this, arguments))
  }
  process.exit(-1);
}

function mkDie() {
  return function(err) {
    if (err != null)
      die(arguments)
  }
}

function log() {
  console.log(fmt.apply(this, arguments));
}

// Setup the devel chezbob.json config
var bobDir = path.dirname(__filename) + "/../bob2k14/"
var deployDir = fs.realpathSync(argv.deploy)
var sodaPort = argv.port_start
var host = "localhost"
var mdbdPort = sodaPort + 1
var vdbdPort = sodaPort + 2
var barcodePort = sodaPort + 3
var barcodeiPort = sodaPort + 4

var sodaEp = fmt("http://%s:%s/api", host, sodaPort);
var mdbdEp = fmt("http://%s:%s", host, mdbdPort);
var vdbdEp = fmt("http://%s:%s", host, vdbdPort);
var barcodeEp = fmt("http://%s:%s", host, barcodePort);
var barcodeiEp = fmt("http://%s:%s", host, barcodeiPort);

var chezbobJSON = {
  sodad: {
    port: sodaPort,
    host: host,
    endpoint: sodaEp
  },
  mdbd: {
    port: mdbdPort,
    host: host,
    endpoint: mdbdEp,
    device: deployDir + "/mdb",
    timeout: 1000
  },
  vdbd: {
    port: vdbdPort,
    host: host,
    endpoint: vdbdEp,
    timeout: 10000,
    device: deployDir + "/vdb"
  },
  barcoded: {
    port: barcodePort,
    host: host,
    endpoint: barcodeEp,
    device: deployDir + "/barcode",
    timeout: 1000
  },
  barcodeid: {
    port: barcodeiPort,
    host: host,
    endpoint: barcodeiEp,
    device: deployDir + "/barcodei",
    timeout: 1000
  },
  db: {
    type: "sqlite",
    path: argv.db
  },
  sodamap: {
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

var columns = {};
var cols = Object.keys(chezbobJSON.sodamap);
cols.sort();

for (var i in cols)
    columns[i] = cols[i];

// Emit the chezbob.json
var jsonPath = deployDir  + "/chezbob.json"
fs.writeFile(jsonPath, JSON.stringify(chezbobJSON, null, 2),
  mkDie("Error writing to %s", jsonPath));

// Kick off servers
var servers = {}
var devices = {}

function ppLog(data) {
  try {
    rec=JSON.parse(data);
    log("%s:%s\[%s\]:", rec.time, rec.name, rec.pid, rec.msg);
  } catch (e) {
    log("%s", data)
  }
}

function startServer(name, path) {
  log(path)
  var srv = spawn("nodejs", [path, jsonPath]);
  srv.on("exit", function(code, sig) { die("Server %s died!", name); })
  srv.stdout.on("data", ppLog);
  srv.stderr.on("data", ppLog);

  servers[name] = srv;
}

function killServer(name) {
  log("Shutting down %s", name);
  servers[name].removeAllListeners("exit");
  servers[name].on("exit", function(code, sig) { die("Server %s shut down", name); })
  servers[name].kill(); 
}

function mkPseudoDevice(name, devFactory, serial) {
  var devPath = deployDir + '/' + name
  var dev = spawn("mkfifo", [devPath])
  if (serial === undefined)
    serial = true;

  if (serial) {
    var port = new serialport(devPath)

    port.on("open",
      function () {
        devices[name] = devFactory(port);
    })
  } else {
    fs.open(devPath, "r+",
      function(err, fd) {
        if (err) die("Couldn't open named pipe %s", devPath);

        devices[name] = devFactory(fd);
      });
  }
}

function ignore() {}

// This implements the soda barcode scanner behavior.
function barcodeFactory(port) {
  var dev = {
    scan: function (barcode, type) {
      var buf = new Buffer(barcode.length + 3);
      if (type === undefined)
        type = "A";

      buf[0] = 0;
      buf[1] = type;
      buf.write(barcode, 2);
      buf[barcode.length + 2] = 0xd;
      
      port.write(buf, function (err, r) {if (err) die("Error scanning barcode");  port.drain(ignore); })
    },
    read: function (d) {
      log(d)
    }
  }
  port.on('data', dev.read);
  return dev;
}

// Implement the Soda Machine
function vdbFactory(port) {
  var dev = {
    send: function(buf) { port.write(buf, function (err, r) { if (err) die("Error sending command %s to vdb server"); port.drain(ignore); }); },
    ack: function() { dev.send(new Buffer([0xa, 0xd])) },
    sendStr: function(s) {
      var buf = new Buffer(s.length + 1);
      buf.write(s, 0, s.length)
      buf[s.length] = 0xd;
      dev.send(buf)
    },
    pressButton: function(col) { dev.sendStr("R00000000" + columns[col]); },
    dispenseSuccess: function(col) { dev.sendStr("K"); },
    dispenseFail: function(col){ dev.sendStr("L"); },
    read: function (d) {
      str = d.toString();
      if (str == "\n\n\n\n\r") {
        log("VDB: Clearing Messages");
        dev.ack();
      } else if (str == "\x1B\r") {
        log("VDB: Reset line 1.");
        dev.ack();
      } else if (str == "W090001\r") {
        log("VDB: Reset line 2.");
        dev.ack();
      } else if (str == "W070001\r") {
        log("VDB: Reset line 3.");
        dev.ack();
      } else if (str == "WFF0000\r") {
        log("VDB: Reset line 4.");
        dev.ack();
      } else if (str == "X\r") { // WTF?
        dev.ack();
      } else if (str == "C\r") { // WTF?
        dev.ack();
      } else if (str == "A\r") { // Authorizing Purchase
        log("Sale AUTHORIZED");
        dev.ack();
      } else if (str == "D\r") { // Denying Purchase
        log("Sale NOT AUTHORIZED");
        dev.ack();
      } else if (str.trim() == "") {
        // Ignore
      } else {
        log("Uknown vdb command: ", d);
      }
    }
  }
  port.on('data', dev.read);
  return dev;
}

// This implements the kiosk barcode scanner behavior.
var characterMap = {};
characterMap["1"] = 2;
characterMap["2"] = 3;
characterMap["3"] = 4;
characterMap["4"] = 5;
characterMap["5"] = 6;
characterMap["6"] = 7;
characterMap["7"] = 8;
characterMap["8"] = 9;
characterMap["9"] = 10;
characterMap["0"] = 11;

function kbInputFactory(port) {
  var dev = {
    keyUp: function (keycode) {
      var buf = new Buffer(24);
      buf.writeUInt32LE(0,0);
      buf.writeUInt32LE(0,8);
      buf.writeUInt16LE(1, 16);
      buf.writeUInt16LE(keycode, 18);
      buf.writeUInt16LE(0, 20);
      fs.writeSync(port, buf, 0, buf.length);
      fs.fsync(port, ignore);
    },
    type: function (ch) { dev.keyUp(characterMap[ch]); },
    scan: function (barcode) {
      for (var i in barcode) {
        dev.type(barcode[i]);
      }
      dev.keyUp(28); // Finish barcode by typing "Enter"
    }
  }
  return dev;
}

// Implement the money-reader
function mdbFactory(port) {
  var dev = {
    send: function(buf) { port.write(buf, function (err, r) { if (err) die("Error sending command %s to vdb server"); port.drain(ignore); }); },
    read: function (d) {
      str = d.toString();
      log("Uknown mdb command: ", d);
    }
  }
  port.on('data', dev.read);
  return dev;
}

// Soda
startServer("soda", bobDir + "/soda_server/app.js")
mkPseudoDevice("barcode", barcodeFactory, true)
startServer("barcode", bobDir + "/barcode_server/app.js")
mkPseudoDevice("barcodei", kbInputFactory, false)
startServer("barcodei", bobDir + "/barcodei_server/app.js")
mkPseudoDevice("vdb", vdbFactory, true)
startServer("vdb", bobDir + "/vdb_server/app.js")
mkPseudoDevice("mdb", mdbFactory, true)
startServer("mdb", bobDir + "/mdb_server/app.js")

// Start Repl
var r = repl.start({
  prompt: "soda>",
})

r.context.scanSoda = function (b, type) {
  devices['barcode'].scan(b, type);
}

r.context.scanTerminal = function (b, type) {
  devices['barcodei'].scan(b, type);
}

r.context.pressSodaButton = function (c) {
  devices['vdb'].pressButton(c);
}

r.context.vendOk = function (c) {
  devices['vdb'].dispenseSuccess(c);
}

r.context.vendFail = function (c) {
  devices['vdb'].dispenseFail(c);
}

r.on("exit",
  function () {
    killServer("mdb");
    killServer("vdb");
    killServer("barcodei");
    killServer("barcode");
    killServer("soda")
  })
