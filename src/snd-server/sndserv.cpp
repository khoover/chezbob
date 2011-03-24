extern "C" {
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <signal.h>
#include <errno.h>
#include <glob.h>
}

#include <boost/format.hpp>

#include "sndserv.h"

#include <string>
#include <sstream>
#include <iostream>

void SndServ::play_sound(const std::string &sound_name)
{
    const std::string base_path("/home/kiosk/sodafw/sounds/");

    std::ostringstream playcmd;

    if (sound_name == "negative_balance")
    {
        playcmd << "ogg123 -q " << base_path << "negative_balance.ogg";
    }
    else if (sound_name == "purchased")
    {
        playcmd << "ogg123 -q " << base_path << "purchased.ogg";
    }
    else
    {
        sio_write(SIO_DEBUG|45, "Unknown sound");
        return;
    }

    system(playcmd.str().c_str());
}

int SndServ::sio_poll(int sleep_for)
{
    char cmd[1024];
    char * cmdv[16];
    int cmdc;
    int cmdlen;

    int stop_num = 0;

    errno = 0;
    if ((cmdlen=sio_read(cmd,sizeof(cmd),sleep_for))>0) {
        cmdc = sio_parse(cmd, cmdv, sizeof(cmdv));

        if (strncmp("SOUND-PLAY", cmdv[0], 10) == 0) {
            play_sound(cmdv[1]);
        }

        if (cmdlen == -1) {
            // server died
            stop_num = errno + 1000;
        };
    }

    return stop_num;
}


int SndServ::report_fail(const char * where,
                         int code, 
                         std::string msg) {

    if (msg == "") {
        switch(code) {
        case 0:
            msg = "bad value";
            break;
        case -1:
            msg = "failed";
            break;
        case -2:
            msg = "timeout";
            break;
        default:
            msg = "unknown";
            break;
        }
    }

    std::string fullmsg = (boost::format("ERROR #%d in %s: %s")
                                    % code % where % msg.c_str()).str();

    sio_write(SIO_DEBUG|45, (char*)fullmsg.c_str());

    return (code<0)?code:-1;
}
