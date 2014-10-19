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

var chezbobJSON = {
  sodad: {
    port: sodaPort,
    host: host,
    endpoint: sodaEp
  },
  mdbd: {
    port: mdbdPort,
    host: host,
    endpoint: mdbdEp
  },
  vdbd: {
    port: vdbdPort,
    host: host,
    endpoint: vdbdEp
  },
  barcoded: {
    port: barcodePort,
    host: host,
    endpoint: barcodeEp,
    device: deployDir + "/barcode",
    timeout: 1000
  },
  db: {
    type: "sqlite",
    path: argv.db
  }
}

// Emit the chezbob.json
var jsonPath = deployDir  + "/chezbob.json"
fs.writeFile(jsonPath, JSON.stringify(chezbobJSON, null, 2),
  mkDie("Error writing to %s", jsonPath));

// Kick off servers
var servers = {}
var devices = {}
function startServer(name, path) {
  log(path)
  var srv = spawn("nodejs", [path, jsonPath]);
  srv.on("exit", function(code, sig) { die("Server %s died!", name); })
  srv.stdout.on("data", function (d) { log("%s: %s", name, d); })
  srv.stderr.on("data", function (d) { log("%s: %s", name, d); })

  servers[name] = srv;
}

function killServer(name) {
  log("Shutting down %s", name);
  servers[name].removeAllListeners("exit");
  servers[name].on("exit", function(code, sig) { die("Server %s shut down", name); })
  servers[name].kill(); 
}

function mkPseudoDevice(name, devFactory) {
  var devPath = deployDir + '/' + name
  var dev = spawn("mkfifo", [devPath])
  var port = new serialport(devPath)

  port.on("open",
    function () {
      var dev = devFactory(port);
      port.on('data', dev.read);
      devices[name] = dev;
    })
}

function ignore() {}

function barcodeFactory(port) {
  return {
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
}

// Soda
startServer("soda", bobDir + "/soda_server/app.js")
mkPseudoDevice("barcode", barcodeFactory)
startServer("barcode", bobDir + "/barcode_server/app.js")

// Start Repl
var r = repl.start({
  prompt: "soda>",
})

r.context.scanSoda = function (b, type) {
  devices['barcode'].scan(b, type);
}

r.on("exit",
  function () {
    killServer("soda")
    killServer("barcode");
  })
