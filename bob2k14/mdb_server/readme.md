# mdb_server daemon

This serve is responsible for running the mdb connection to the 
bill reader and the coin collector.

It uses JSON-RPC to talk to the main soda server.

My apologies that it is written in javascript (er, typescript).
The old version was written in python, but it had cpu usage issues.

# Building

The build system for the mdb_server uses gulp. 
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
is cb_mdbd, and you should start is as:

    service cb_mdbd start

The logs are stored in /var/log/chezbob/cb_mdbd.log, so to view them
using bunyan:

    cat /var/log/chezbob/cb_mdbd.log | bunyan

# Interface

The JSON-RPC endpoint exposes one interface, Mdb.command which takes
a command string that gets sent directly to the P115E MDB adapter.
The result of the command is returned.

The script takes care of resetting all the devices automatically when
the service starts.

# References

TODO: a reference to the P115E MDB protocol goes here.
