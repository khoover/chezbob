# fp_server daemon

This server is responsible for running the fingerprint connection to
the soda UI.

It uses node-libfprint, (https://github.com/no2chem/node-libfprint)
a node wrapper for libfprint (http://www.freedesktop.org/wiki/Software/fprint/),
to interface with the fingerprint reader.

It uses JSON-RPC to talk to the main soda server.

My apologies that it is written in javascript (er, typescript).
The old version was written in python, but it had cpu usage issues.

# Building

The build system for the barcode_server uses gulp. 
To initalize an empty checkout, first restore the npm modules:

    npm install

Ensure bunyan, typescript and gulp are installed globally:

    sudo su
    npm install -g typescript
    npm install -g gulp
    npm install -g bunyan

Then, run gulp.

    gulp

The javascript source will be located in the build directory.

# Running

Start app.js to run the server:

    nodejs app.js

Messages are emitted as json, which probably is annoying to decipher
if you aren’t a computer (or a piece of javascript). To get useful
output, pipe to bunyan:

    nodejs app.js | bunyan

Most likely you are not running this script directly, but as a service.
In that case, if you deployed using ansible, the name of the service
is cb_barcoded, and you should start it as:

    service cb_fpd start

The logs are stored in /var/log/chezbob/cb_barcoded.log, so to view them
using bunyan:

    cat /var/log/chezbob/cb_fpd.log | bunyan

