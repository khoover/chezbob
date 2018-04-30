#!/usr/bin/python3

from enum import Enum
from aiohttp import web
import asyncio
import fprint
import json

import bob_send
import private_api

class FingerprintState(Enum):
    IDLE = 0
    ENROLLING = 1
    ENROLL_STARTING = 2
    IDENTIFYING = 3
    IDENTIFY_STARTING = 4

class FingerprintInterface:
    dev = None
    state = FingerprintState.IDLE
    userids = []
    templates = []
    enrolling_userid = None

    def __init__(self):
        # These are here to avoid refcounting hell
        # TODO: Fix this in the fprint API
        self.bound_enroll_progress_callback = self.enroll_progress_callback
        self.bound_identify_callback = self.identify_callback
        self.bound_stop_callback = self.stop_callback

        db = private_api.db.get_conn("/home/supersat/db.conf")
        self.db_api = private_api.bob_api.BobApi(db)
        self.load_db()
        endpoint = "http://127.0.0.1:8080/api"
        self.send_api = bob_send.BobApi(endpoint, 1, 0)

        self.loop = asyncio.get_event_loop()
        fprint.init()
        ddevs = fprint.DiscoveredDevices()
        if len(ddevs) != 1:
            raise Exception("Unexpected number of fingerprint devices: {0}".format(len(ddevs)))
        self.dev = fprint.Device.open(ddevs[0])
        fds = self.dev.get_pollfds()
        for fd in fds:
            if fd[1] == 1:
                self.loop.add_reader(fd[0], self.dev.handle_events)
            if fd[1] == 4:
                self.loop.add_writer(fd[0], self.dev.handle_events)
        print("FingerprintInterface initialized")

    def load_db(self):
        self.userids = []
        self.templates = []
        rows = self.db_api.get_fingerprint_data()
        for row in rows:
            self.userids.append(row[1])
            pd = fprint.PrintData.from_data(bytes(row[2]))
            self.templates.append(pd)

    def reload_db(self):
        self.load_db()
        if self.state == FingerprintState.IDENTIFYING:
            self.state = FingerprintState.IDENTIFY_STARTING
            print("State is IDENTIFY_STARTING")
            self.cancel_identify()

    def enroll_progress_callback(self, result, pd):
        if result == fprint.fp_enroll_result.FP_ENROLL_COMPLETE:
            self.cancel_enroll()
            self.userids.append(self.enrolling_userid)
            self.templates.append(pd)
            self.db_api.add_fingerprint_data(self.enrolling_userid, pd.data)
        if result == fprint.fp_enroll_result.FP_ENROLL_FAIL:
            self.cancel_enroll()
        self.send_api.send_enroll_progress(result)

    def _start_enroll(self):
        print("_start_enroll")
        self.dev.enroll_start(self.bound_enroll_progress_callback)
        self.state = FingerprintState.ENROLLING
        print("State is now ENROLLING")

    def begin_enroll(self, enrolling_userid):
        print("begin_enroll")
        self.enrolling_userid = enrolling_userid
        if self.state != FingerprintState.IDLE:
            self._cancel()
            self.state = FingerprintState.ENROLL_STARTING
            print("State is now ENROLL_STARTING")
        else:
            self._start_enroll()

    def cancel_enroll(self):
        print("cancel_enroll")
        self.dev.enroll_stop(self.bound_stop_callback)

    def identify_callback(self, result, offset):
        print("Identify callback: {0} {1}".format(result, offset))
        userid = -1
        if result == 1:
            userid = self.userids[offset]
        else:
            self.state = FingerprintState.IDENTIFY_STARTING
            print("State is now IDENTIFY_STARTING")
        self.send_api.send_identify_result(result, userid)
        self.cancel_identify()

    def _start_identify(self):
        self.dev.identify_start(self.bound_identify_callback, self.templates)
        self.state = FingerprintState.IDENTIFYING
        print("State is now IDENTIFYING")

    def begin_identify(self):
        print("begin_identify")
        if self.state != FingerprintState.IDLE:
            self._cancel()
            self.state = FingerprintState.IDENTIFY_STARTING
            print("State is now IDENTIFY_STARTING")
        else:
            self._start_identify()

    def cancel_identify(self):
        print("cancel_identify")
        self.dev.identify_stop(self.bound_stop_callback)

    def stop_callback(self):
        if self.state == FingerprintState.ENROLLING:
            self.enrolling_userid = None
        if self.state == FingerprintState.ENROLL_STARTING:
            self.loop.call_soon(self._start_enroll)
        if self.state == FingerprintState.IDENTIFY_STARTING:
            self.loop.call_soon(self._start_identify)
        self.state = FingerprintState.IDLE
        print("State is IDLE")

    def _cancel(self):
        print("_cancel")
        if self.state == FingerprintState.ENROLLING:
            self.cancel_enroll()
        elif self.state == FingerprintState.IDENTIFYING:
            self.cancel_identify()

    def idle(self):
        print("idle")
        self._cancel()
        self.state = FingerprintState.IDLE
        print("State is now IDLE")

class FingerprintDaemon:
    def __init__(self):
        self.fp_interface = FingerprintInterface()
        self.app = web.Application()
        self.app.add_routes([web.post('/', self.rpc),
                            web.get('/enroll/{uid}', self.enroll),
                            web.get('/identify', self.identify)])

    def run(self):
        self.fp_interface.begin_identify()
        web.run_app(self.app, port=8089)

    async def rpc(self, request):
        request = await request.text()
        request = json.loads(request)
        if request['method'] == 'fp.identify':
            self.fp_interface.begin_identify()
        elif request['method'] == 'fp.enroll':
            self.fp_interface.begin_enroll(request['params'][0])
        elif request['method'] == 'fp.idle':
            self.fp_interface.idle()
        elif request['method'] == 'fp.reload':
            self.fp_interface.reload_db()
        return web.Response()

    async def enroll(self, request):
        uid = request.match_info.get('uid', None)
        self.fp_interface.begin_enroll(uid)
        return web.Response(text="enrolling")

    async def identify(self, request):
        self.fp_interface.begin_identify()
        return web.Response(text="identifying")

def main():
    daemon = FingerprintDaemon()
    daemon.run()

if __name__ == '__main__':
    main()
