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

var columns = { "00": 0.05, "01": 0.1, "02": 0.25}

exports.mdbFactory = function(port) {
  var dev = {
    send: function(buf) { port.write(buf, function (err, r) { if (err) die("Error sending command %s to mdb server"); port.drain(com.ignore); }); },
    ack: function() { dev.send(new Buffer([0xa])) },
    sendStr: function(s) {
      var buf = new Buffer(s.length + 1);
      buf.write(s, 0, s.length)
      buf[s.length] = 0xd;
      dev.send(buf)
    },
    ackAndReply: function(r) { dev.ack(); dev.sendStr(r); },
    tubeToValue: columns,
    valueToTube: com.invert(columns),
    read: function (d) {
      str = d.toString().trim();
      log("MDB:", str);

      // COIN GIVER SETUP
      if (str == "R1") { // TODO: Reset Coin Giver, disable coin dispensing
        dev.ackAndReply("Z");
      } else if (str[0] == "N") { // TODO: Enable Individual Coin Type Accept
        dev.ackAndReply("Z");
      } else if (str[0] == "M") { // TODO: Enable Manual Coin Dispense 
        dev.ackAndReply("Z");
      } else if (str == "P1") { // TODO: Poll Coingiver - optionally return more than Z
        dev.ackAndReply("Z");
      } else if (str == "E1") { // TODO: Enable Coin Acceptance (apply settings)
        dev.ackAndReply("Z");
      

      // BILL VALIDATOR SETUP
      } else if (str == "R2") { // TODO: Reset Bill Validator, disable bill acceptance, 
        dev.ackAndReply("Z");
      } else if (str == "P2") { // TODO: Poll Bill Validator
        dev.ackAndReply("Z");
      } else if (str[0] == "L") { // TODO: Individual Bill Type Inhibit
        dev.ackAndReply("Z");
      } else if (str[0] == "V") { // TODO: Set security levels for bill type
        dev.ackAndReply("Z");
      } else if (str[0] == "J") { // TODO: Individual Bill Escrow setting
        dev.ackAndReply("Z");
      } else if (str[0] == "E2") { // TODO: Enable Bill Acceptance (apply settings)
        dev.ackAndReply("Z");
      } else if (str[0] == "G") { // TODO: Enable Bill Acceptance (apply settings)
        v = dev.tubeToValue[str.substring(1,3)]
        console.log("Returning coin of value " + v)
        dev.ackAndReply("Z");
      } else if (str == "") { // Ignore
      } else {
        log("Uknown mdb command: ", str);
      }
    },
    putCoin: function(value) {
      var t = dev.valueToTube[value];
      if (t == undefined)
        throw "Bad coin value " + value + 
                            " must be one of 0.05, 0.1, 0.25"
      dev.sendStr("P1 " + t)
    },
    pressCoinReturn: function() {
      dev.sendStr("W");
    }
  }
  port.on('data', dev.read);
  return dev;
}
