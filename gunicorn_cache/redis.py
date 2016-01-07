#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import
from datetime import datetime
import re
import socket
import sys

try:
    import cPickle as pickle
except ImportError:
    import pickle

import gunicorn.http.wsgi as wsgi
from gunicorn.workers.sync import SyncWorker
from gunicorn import six
from redis import Redis


class RedisWorker(SyncWorker):

    def __init__(self, *args, **kwargs):
        super(RedisWorker, self).__init__(*args, **kwargs)
        # reload conf
        self.app.reload()
        self.cfg = self.app.cfg
        self.redis = Redis.from_url(self.cfg.cache_store.get('redis_url', "redis://127.0.0.1/0"))
        self.cache_route = self.cfg.cache_route

    def handle_request(self, listener, req, client, addr):
        environ = {}
        resp = None
        try:
            self.cfg.pre_request(self, req)
            request_start = datetime.now()
            resp, environ = wsgi.create(req, client, addr,
                                        listener.getsockname(), self.cfg)
            # Force the connection closed until someone shows
            # a buffering proxy that supports Keep-Alive to
            # the backend.
            resp.force_close()
            self.nr += 1
            if self.nr >= self.max_requests:
                self.log.info("Autorestarting worker after current request.")
                self.alive = False

            use_cache = False
            cache_key = "{0}:{1}".format(req.uri, req.method)
            for route in self.cache_route:
                if re.match(route['url'], req.uri) and req.method in route["methods"]:
                    use_cache = True
                    if environ.get('HTTP_GUNICORN_CACHE_REFRESH'):
                        result = None
                    else:
                        result = self.redis.get(cache_key)
                    if not result:
                        respiter = self.wsgi(environ, resp.start_response)
                        if resp.status_code == 200:
                            result = {'body': [x for x in respiter], 'headers': resp.headers}
                            self.redis.set(cache_key, pickle.dumps(result), route.get("expire", 300))
                    else:
                        result = pickle.loads(result)
                        if resp.status is None:
                            resp.start_response('200 OK', result['headers'])
                        respiter = result['body']
                        if route.get("prolong", True):
                            self.redis.expire(cache_key, route.get("expire", 300))
                    break
            if not use_cache:
                respiter = self.wsgi(environ, resp.start_response)
            try:
                if isinstance(respiter, environ['wsgi.file_wrapper']):
                    resp.write_file(respiter)
                else:
                    for item in respiter:
                        resp.write(item)
                resp.close()
                request_time = datetime.now() - request_start
                self.log.access(resp, req, environ, request_time)
            finally:
                if hasattr(respiter, "close"):
                    respiter.close()
        except socket.error:
            exc_info = sys.exc_info()
            # pass to next try-except level
            six.reraise(exc_info[0], exc_info[1], exc_info[2])
        except Exception:
            if resp and resp.headers_sent:
                # If the requests have already been sent, we should close the
                # connection to indicate the error.
                self.log.exception("Error handling request")
                try:
                    client.shutdown(socket.SHUT_RDWR)
                    client.close()
                except socket.error:
                    pass
                raise StopIteration()
            raise
        finally:
            try:
                self.cfg.post_request(self, req, environ, resp)
            except Exception:
                self.log.exception("Exception in post_request hook")
