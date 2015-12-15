===============================
Gunicorn Cache
===============================

.. image:: https://img.shields.io/travis/youngking/gunicorn_cache.svg
        :target: https://travis-ci.org/youngking/gunicorn_cache

.. image:: https://img.shields.io/pypi/v/gunicorn_cache.svg
        :target: https://pypi.python.org/pypi/gunicorn_cache


Cache worker for gunicorn

* Free software: ISC license


Usage
-------

Add these settings in Gunicorn configuration file:

::

        cache_route = {'^/custom_url1': {
                'methods': ['GET', 'POST'],
                'expire': 500
            },
            '^/custom_url2$':{
                'methods': ['POST'],
                'expire': 500
            }
        }

        cache_store = {'redis_url':'redis://127.0.0.1:6379/0'}

        worker_class = 'gunicorn_cache.RedisWorker'


Then run the gunicorn.



Features
--------

* TODO
