// Takes a serial port, returns an object with attributes:
//
// send(buf) - sends the buffer buf down the serial port
// ack() - sends an ack ("0xa0xd")
// sendStr() - sends a string (completes it with "0xd")
// read(d) - callback for reading incomming commands from the port
//
var com = require("./common")

var log = com.log
var die = com.die

var columns = {
  0: "01",
  1: "02",
  2: "03",
  3: "04",
  4: "05",
  5: "06",
  6: "07",
  7: "08",
  8: "09",
  9: "0A",
}

// Implement the Soda Machine
exports.vdbFactory = function (port) {
  var dev = {
    send: function(buf) { port.write(buf, function (err, r) { if (err) die("Error sending command %s to vdb server"); port.drain(function(){}); }); },
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
