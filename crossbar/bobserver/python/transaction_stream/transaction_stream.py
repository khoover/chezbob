import datetime
import decimal
import threading

from twisted.internet.defer import inlineCallbacks
from twisted.logger import Logger

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.exception import ApplicationError

from . import listen_transactions as trans_listener

NODE_NAME = 'transaction_streamer'


def prepare_record(obj):
    if not obj:
        return dict()

    for x in obj.keys():
        if type(obj[x]) == datetime.datetime:
            obj[x] = obj[x].isoformat()
        if type(obj[x]) == decimal.Decimal:
            obj[x] = float(obj[x])
    return dict(obj)


class AppSession(ApplicationSession):

    log = Logger()

    @inlineCallbacks
    def body(self):
        yield self.heartbeat()

        # CALL a remote procedure
        #
        #try:
        #    res = yield self.call('com.example.mul2', 8, 3)
        #    self.log.info("mul2() called with result: {result}",
        #                  result=res)
        #except ApplicationError as e:
        #    # ignore errors due to the frontend not yet having
        #    # registered the procedure we would like to call
        #    if e.error != 'wamp.error.no_such_procedure':
        #        raise e

        yield sleep(1)

    def heartbeat(self):
        return self.publish('chezbob.heartbeat', NODE_NAME)

    #def onhello(self, msg):
    #    self.log.info("event for 'onhello' received: {msg}", msg=msg)

    def add2(self, x, y):
        self.log.info("add2() called with {x} and {y}", x=x, y=y)
        return x + y

    def handle_transaction(self, curs, tid):
        record = trans_listener.get_detailed_details(curs, tid)

        record = prepare_record(record)
        return self.publish('chezbob.transaction', record)

    def listen_thread(self):
        self.log.info("Started listening thread")
        trans_listener.watch_transactions(self.handle_transaction)

    def start_thread(self):
        self.thread = threading.Thread(daemon=True, target=self.listen_thread)
        self.thread.start()

    @inlineCallbacks
    def onJoin(self, details):
        self.log.info("Starting transaction streamer...")

        # SUBSCRIBE to a topic and receive events
        #
        #yield self.subscribe(self.onhello, 'com.example.onhello')
        #self.log.info("subscribed to topic 'onhello'")

        #yield self.register(self.add2, 'com.example.add2')
        #self.log.info("procedure add2() registered")
        # Throws ApplicationError with e.error ==
        # 'wamp.error.procedure_already_exists' if already registered

        self.start_thread()

        while True:
            for x in self.body():
                yield x



