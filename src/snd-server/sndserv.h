#ifndef _MDBSERV_H_
#define _MDBSERV_H_

#define VERSION   "0.00"

#include <algorithm>
#include <string>
#include <cerrno>

extern "C" {
#include <glob.h>
#include <string.h>
}

#include <algorithm>
#include <iostream>
using std::min;
#include "servio.h"
#include "sercom.h"
using std::max;
using std::min;


class SndServ
{
public:
    SndServ(int argc, char**argv)
    {

        if (sio_open(argc, argv, "SNDSERV", VERSION, "") < 0) {
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
    }

    int report_fail(const char * where,
                    int code = 0,
                    const std::string msg = "");

    int sio_poll(int sleep_for);

    void play_sound(const std::string &sound_name);

private:
};

#endif
