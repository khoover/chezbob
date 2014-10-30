
// Takes a serial port, returns an object with attributes:
//
// send(buf) - sends the buffer buf down the serial port
// ack() - sends an ack ("0xa0xd")
// sendStr() - sends a string (completes it with "0xd")
// read(d) - callback for reading incomming commands from the port
//
var com = require("./common")

// This implements the soda barcode scanner behavior.
exports.barcodeFactory = function (port) {
  var dev = {
    scan: function (barcode, type) {
      var buf = new Buffer(barcode.length + 3);
      if (type === undefined)
        type = "A";

      buf[0] = 0;
      buf[1] = type;
      buf.write(barcode, 2);
      buf[barcode.length + 2] = 0xd;
      
      port.write(buf,
        function (err, r) {
          if (err) com.die("Error scanning barcode");
          port.drain(com.ignore);
        })
    },
    read: function (d) {
      com.log(d)
    }
  }
  port.on('data', dev.read);
  return dev;
}
