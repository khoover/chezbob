#!/usr/bin/python3

from enum import Enum
from aiohttp import web
import asyncio
import fprint
import json
import os
import sys

DEFAULT_ENDPOINT = "http://192.168.1.10:8080/api"

BOB_PATH = os.environ.get('CHEZ_BOB_PATH', '/git')
sys.path.insert(0, os.path.join(BOB_PATH, 'pybob'))

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

        db = private_api.db.get_conn()
        self.db_api = private_api.bob_api.BobApi(db)
        self.load_db()
        endpoint = DEFAULT_ENDPOINT
        self.send_api = bob_send.BobApi(endpoint, 1, 0)

        self.loop = asyncio.get_event_loop()
        fprint.init()
        ddevs = fprint.DiscoveredDevices()
        if len(ddevs) != 1:
            raise Exception(
                "Unexpected number of fingerprint devices: {0}".format(
                    len(ddevs)))
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
        self.dev.enroll_start(self.bound_enroll_progress_callback)
        self.state = FingerprintState.ENROLLING

    def begin_enroll(self, enrolling_userid):
        self.enrolling_userid = enrolling_userid
        if self.state != FingerprintState.IDLE:
            self._cancel()
            self.state = FingerprintState.ENROLL_STARTING
        else:
            self._start_enroll()

    def cancel_enroll(self):
        self.dev.enroll_stop(self.bound_stop_callback)

    def identify_callback(self, result, offset):
        userid = -1
        if result == 1:
            userid = self.userids[offset]
        else:
            self.state = FingerprintState.IDENTIFY_STARTING
        self.send_api.send_identify_result(result, userid)
        self.cancel_identify()

    def _start_identify(self):
        self.dev.identify_start(self.bound_identify_callback, self.templates)
        self.state = FingerprintState.IDENTIFYING

    def begin_identify(self):
        if self.state != FingerprintState.IDLE:
            self._cancel()
            self.state = FingerprintState.IDENTIFY_STARTING
        else:
            self._start_identify()

    def cancel_identify(self):
        self.dev.identify_stop(self.bound_stop_callback)

    def stop_callback(self):
        if self.state == FingerprintState.ENROLLING:
            self.enrolling_userid = None
        if self.state == FingerprintState.ENROLL_STARTING:
            self.loop.call_soon(self._start_enroll)
        if self.state == FingerprintState.IDENTIFY_STARTING:
            self.loop.call_soon(self._start_identify)
        self.state = FingerprintState.IDLE

    def _cancel(self):
        if self.state == FingerprintState.ENROLLING:
            self.cancel_enroll()
        elif self.state == FingerprintState.IDENTIFYING:
            self.cancel_identify()

    def idle(self):
        self._cancel()
        self.state = FingerprintState.IDLE


class FingerprintDaemon:
    def __init__(self):
        self.fp_interface = FingerprintInterface()
        self.app = web.Application()
        self.app.router.add_routes([web.post('/', self.rpc),
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
