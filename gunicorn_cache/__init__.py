# -*- coding: utf-8 -*-

__author__ = 'Young King'
__email__ = 'yanckin@gmail.com'
__version__ = '0.1.0'

from gunicorn.config import Setting, validate_dict
from .redis import RedisWorker


class CacheStore(Setting):
    name = "cache_store"
    section = "Cache Store"
    validator = validate_dict
    default = {
        'redis_url': 'redis://127.0.0.1:6379/0'
    }
    desc = """
    Cache Store Config
    """


def validate_list_dict(val):
    if not isinstance(val, list):
        raise TypeError("Not a list: %s" % val)
    return [validate_dict(i) for i in val]


class CacheRoute(Setting):
    name = "cache_route"
    section = "Cache Route"
    validator = validate_list_dict
    desc = """
    Cache Route Config
    """


