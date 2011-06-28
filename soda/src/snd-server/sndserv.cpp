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
#include <boost/lexical_cast.hpp>

#include "sndserv.h"

#include <string>
#include <sstream>
#include <iostream>

using namespace std;
using boost::format;
using boost::lexical_cast;
using boost::bad_lexical_cast;

bool SndServ::play_sound(const std::string &sound_name)
{
    if (_sounds.find(sound_name) == _sounds.end())
    {
        report_debug(string("Unknown sound:")+sound_name);
        return true;
    }

    float volume = _volumes["_master"];

    if (_volumes.find(sound_name) != _volumes.end())
        volume *= _volumes[sound_name];

    if (volume > 1)
    {
        ostringstream grr;
        grr << "volume for " << sound_name << " > 1: " << volume;
        report_debug((format("volume for %s > 1: %f")
                             % sound_name % volume).str());
    }

    std::ostringstream playcmd;

    playcmd << format("amixer -q sset 'Master' %d%%;") % int(volume * 100);
    playcmd << "ogg123 -q " << _vars["base_path"] << _sounds[sound_name];

    if (_verbose) std::cerr << playcmd.str() << std::endl;

    return system(playcmd.str().c_str()) == 0;
}

bool SndServ::set_var(const std::string &var, const std::string &value)
{
    if (var.substr(0, 6) == "volume")
    {
        float volume;

        try {
            volume = lexical_cast<float>(value);
        } catch (bad_lexical_cast&) {
            return false;
        }

        if (_verbose)
            std::cerr << "setting " << var << " to " << volume << std::endl;

        if (var == "volume") _volumes["_master"] = volume;
        else {
            string sub = var.substr(7, string::npos);
            if (_volumes.find(sub) == _volumes.end()) {
                report_debug((format("inappropriate volume selector %s")
                                     % sub).str());
                return false;
            }
            _volumes[sub] = volume;
        }
    }
    else
    {
        if (_vars.find(var) != _vars.end())
            _vars[var] = value;
        else
            return false;
    }

    return true;
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

        if (_verbose) std::cerr << cmd << std::endl;

        cmdc = sio_parse(cmd, cmdv, sizeof(cmdv));

        if (strncmp("SOUND-PLAY", cmdv[0], 10) == 0) {
            play_sound(cmdv[1]);
        } else if (strncmp("SYS-SET", cmdv[0], 7) == 0 && _name == cmdv[1]){
            if (cmdv[2] && cmdv[3] && cmdv[4])
            {
                std::cerr << "set " << cmdv[2] << " = " << cmdv[4] << std::endl;
                if (!set_var(cmdv[2], cmdv[4]))
                    report_debug((format("set var failed %s = %s")
                                        % cmdv[2] % cmdv[4]).str());
            }
        }


        if (cmdlen == -1) {
            // server died
            stop_num = errno + 1000;
        };
    }

    return stop_num;
}

int SndServ::report_debug(const std::string &msg)
{
    sio_write(SIO_DEBUG|45, (char*)msg.c_str());
}
