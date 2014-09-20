// This file is a simple launcher for the built app

var built = require('./build/server.js');
var app = new built.App();
app.main(process.argv.slice(2));
