// Takes a serial port, returns an object with attributes:
//
// send(buf) - sends the buffer buf down the serial port
// ack() - sends an ack ("0xa0xd")
// sendStr() - sends a string (completes it with "0xd")
// read(d) - callback for reading incomming commands from the port
//
var com = require("./common")
var fs = require("fs")

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

exports.kbdFactory = function(port) {
  var dev = {
    keyUp: function (keycode) {
      var buf = new Buffer(24);
      buf.writeUInt32LE(0,0);
      buf.writeUInt32LE(0,8);
      buf.writeUInt16LE(1, 16);
      buf.writeUInt16LE(keycode, 18);
      buf.writeUInt16LE(0, 20);
      fs.writeSync(port, buf, 0, buf.length);
      fs.fsync(port, function () {});
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
