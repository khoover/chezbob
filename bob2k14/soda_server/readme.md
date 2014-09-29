# soda_server daemon

This server is responsible for running the soda machine UI.

It uses JSON-RPC to talk to other endpoints. This will eventually
be replaced with a redis RPC engine to eliminate random ports
all over the server.

My apologies that it is written in javascript (er, typescript).
The old version was written in python, but it had cpu usage issues.
If you feel like rewriting it in a more fun language like Go,
while fixing all the bugs, be my guest :).

# Building

The build system for the soda_server uses gulp.
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
is cb_vdbd, and you should start it as:

    service cb_vdbd start

The logs are stored in /var/log/chezbob/cb_sodad.log, so to view them
using bunyan:

    cat /var/log/chezbob/cb_sodad.log | bunyan

# Interface

There are two components to sodad, the user interface (UI), and the server.
The UI talks to the server using bidirectional websockets.

More about this interface to follow shortly.

# References

