"""A simple logging-compatible handler for logging to redis."""
# Copied and modified from https://gist.github.com/hellp/2428204

import logging
import traceback
import sys

import redis
import simplejson


class RedisHandler(logging.Handler):
    """A logging-compatible handler for logging to redis."""
    def __init__(self, prefix, lname, conn, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.lname = lname
        self.channel = prefix + ":log:" + lname
        self.redis_conn = conn

    def format(self, record):
        dict_record = {
            "args": record.args,
            "created": record.created,
            "filename": record.filename,
            "funcName": record.funcName,
            "msg": record.msg,
            "level": record.levelname,
            "lineno": record.lineno,
            "module": record.module,
            "name": record.name,
            "pathname": record.pathname,
            "pid": record.process,
            "processName": record.processName,
            "threadName": record.threadName,
            "thread": record.thread,
            "msecs": record.msecs,
            "exc_info":
                traceback.format_exception(*record.exc_info)
                    if record.exc_info else None,
            "exc_text": record.exc_text,
        }
        return simplejson.dumps(dict_record)

    def emit(self, record):
        msg = self.format(record)
        try:
            (self.redis_conn.pipeline()
             .publish(self.channel, msg)
             .rpush(self.channel, msg)
             .ltrim(self.channel, -1000, -1)  # keep only the last 1000 entries
             .execute())
        except redis.RedisError:
            pass

def main():
    # Usage example
    import socket

    host = socket.gethostname().split('.')[0]
    fmt = '%(asctime)s  {0}  %(name)s  %(levelname)s  %(message)s'.format(host)
    #logging.basicConfig(format=fmt, level=logging.INFO)
    logger = logging.getLogger(__name__)
    handler = RedisHandler(
        'prefix', 'foolog', redis.StrictRedis('localhost'))
    #handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.info('Logger set up.')
    try:
        raise Exception("Test")
    except:
        logger.exception("thrown")


if __name__ == '__main__':
    sys.exit(main())
