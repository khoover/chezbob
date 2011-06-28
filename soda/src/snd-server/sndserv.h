#ifndef _MDBSERV_H_
#define _MDBSERV_H_

#include <algorithm>
#include <string>
#include <cerrno>
#include <algorithm>
#include <iostream>
#include <map>

extern "C" {
#include <glob.h>
#include <string.h>
}

using std::min;
#include "servio.h"
#include "sercom.h"
using std::max;
using std::min;


class SndServ
{
public:
    SndServ(int argc, char**argv)
        :_verbose(false), _name("SNDSERV"), _version("1.0")
    {

        if (sio_open(argc, argv, _name.c_str(), _version.c_str(), "") < 0) {
            exit(11);
        };

        sio_write(SIO_DATA, "SYS-ACCEPT\tSOUND-\tSYS-SET");

        init();
    }

    ~SndServ()
    {
    }

    void init()
    {
        _vars["base_path"] = "/home/kiosk/sodafw/sounds/";

        _sounds["negative_balance"] = "negative_balance.ogg";
        _sounds["purchased"] = "purchased.ogg";

        _volumes["_master"] = 0.7;
        _volumes["purchased"] = 0.7;
        _volumes["negative_balance"] = 1.0;
    }

    int report_debug(const std::string &msg);
    int sio_poll(int sleep_for);

    bool play_sound(const std::string &sound_name);
    bool set_var(const std::string &var, const std::string &value);

private:
    bool _verbose;
    std::string _name;
    std::string _version;

    std::map<std::string, std::string> _sounds;
    std::map<std::string, std::string> _vars;
    std::map<std::string, float> _volumes;
};

#endif
