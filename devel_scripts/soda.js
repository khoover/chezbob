#! /usr/bin/env node
var usage = " soda --deploy <deploy dir> --db <path-to-database> --port_start [num] --logs [file|terminal|null]"
// Library Imports
var util = require("util")
var argv = require("optimist")
           .usage(usage)
           .default("port_start", 8080)
           .default("logs", "file")
           .describe("deploy", "Directory where temporary files for the current deployment are held")
           .describe("db", "Path to the sqlite3 version of ChezBob's database to use")
           .describe("port-start", "Starting port number for the deployed daemons")
           .describe("logs", "Where to print logs from started daemons. With file each process's logs are printed in its own file. With terminal they are all printed in the current terminal. With null they are all ignored")
           .demand(["deploy", "db", "port_start", "logs"])
           .check(function (args) {
              if (args.logs != "file" &&
                  args.logs != "terminal" &&
                  args.logs !=  "null")
                throw "Invalid value for logs: " + args.logs
            })
           .argv
var fs = require("fs")
var spawn = require("child_process").spawn
var repl = require("repl")
var path = require("path")
var serialport = require("serialport").SerialPort
var com = require("./common")

// Utility functions
var fmt = util.format
var ignore = com.ignore
var die = com.die
var log = com.log

function mkDie() {
  return function(err) {
    if (err != null)
      die(arguments)
  }
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

// Emit the chezbob.json
var jsonPath = deployDir  + "/chezbob.json"
fs.writeFile(jsonPath, JSON.stringify(chezbobJSON, null, 2),
  mkDie("Error writing to %s", jsonPath));

// Kick off servers
var servers = {}
var devices = {}
var socats = {}

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
  var childIO;

  if (argv.logs == "file") {
    stdoutFD = fs.openSync(deployDir + "/" + name + ".stdout", "w")
    stderrFD = fs.openSync(deployDir + "/" + name + ".stderr", "w")
    childIO = ["pipe", stdoutFD, stderrFD]
  } else if (argv.logs == "terminal") {
    childIO = "pipe";
  } else { //null
    childIO = "ignore";
  }

  var srv = spawn("nodejs", [path, jsonPath], {stdio: childIO});
  srv.on("exit", function(code, sig) { die("Server %s died!", name); })

  if (argv.logs == "terminal") {
    srv.stdout.on("data", ppLog);
    srv.stderr.on("data", ppLog);
  }

  servers[name] = srv;
}

function killServer(name) {
  log("Shutting down %s", name);
  servers[name].removeAllListeners("exit");
  servers[name].on("exit", function(code, sig) { die("Server %s shut down", name); })
  servers[name].kill(); 
}

function makePTTYPair(name, cb) {
  socats[name] = spawn("socat", ['-d', '-d', 'pty,raw,echo=0', 'pty,raw,echo=0']);
  var pttyReg = new RegExp('PTY is (\/dev\/pts\/[0-9]*)', 'g')

  var ptyPaths = [];
  socats[name].stderr.on("data", function(d) {
    if (ptyPaths.length >= 2) return; // Only interested in the 1st 2 occurances
    var s = d.toString();
    m = pttyReg.exec(s);

    while (m != null) {
      ptyPaths.push(m[1]);
      m = pttyReg.exec(s);

      if (ptyPaths.length == 2) cb(ptyPaths);
    }
  });
}

function mkPseudoDevice(name, devFactory, serial) {
  makePTTYPair(name,
    function(ptys) {
      var devPath = deployDir + '/' + name

      if (serial === undefined)
        serial = true;

      var master = ptys[0]
      var slave = ptys[1]

      // Link the slave
      fs.unlink(devPath,
        function (err) {
          if (err && fs.existsSync(devPath)) die("Couldn't remove ", devPath);
          fs.symlinkSync(slave, devPath);
      })

      // Fire off the pseudo device on the master
      if (serial) {
        var port = new serialport(master)

        port.on("open",
          function () {
            devices[name] = devFactory(port);
        })
      } else {
        fs.open(master, "r+",
          function(err, fd) {
            if (err) die("Couldn't open named pipe %s", devPath);
    
            devices[name] = devFactory(fd);
          });
      }
    })
}

function killPseudoDevice(name) {
  socats[name].kill();
}

// Soda
startServer("soda", bobDir + "/soda_server/app.js")
mkPseudoDevice("barcode", require("./barcode.js").barcodeFactory, true)
startServer("barcode", bobDir + "/barcode_server/app.js")
mkPseudoDevice("barcodei", require("./kbd.js").kbdFactory, false)
startServer("barcodei", bobDir + "/barcodei_server/app.js")
mkPseudoDevice("vdb", require("./vdb.js").vdbFactory, true)
startServer("vdb", bobDir + "/vdb_server/app.js")
mkPseudoDevice("mdb", require("./mdb.js").mdbFactory, true)
startServer("mdb", bobDir + "/mdb_server/app.js")

// Start Repl
var r = repl.start({
  prompt: "soda>",
})

// Additional functions to the repl to interact with devices
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

r.context.putCoin = function (v) {
  devices['mdb'].putCoin(v);
}

r.context.pressCoinReturn = function (v) {
  devices['mdb'].pressCoinReturn(v);
}

r.on("exit",
  function () {
    killServer("mdb");
    killServer("vdb");
    killServer("barcodei");
    killServer("barcode");
    killServer("soda")
    killPseudoDevice("barcode");
    killPseudoDevice("barcodei");
    killPseudoDevice("vdb");
    killPseudoDevice("mdb");
  })
