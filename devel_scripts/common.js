var util = require("util")

exports.invert = function(o) {
  var ret = {}
  for (var k in o) {
    if (o.hasOwnProperty(k))
      ret[o[k]] = k;
  }
  return ret;
}

exports.log = function () {
  console.log(util.format.apply(this, arguments));
}

exports.die = function () {
  if (arguments.length > 0) {
    log(arguments)
  }

  process.exit(-1);
}

exports.ignore = function () {}
