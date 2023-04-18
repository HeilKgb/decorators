#!/usr/bin/env python3

import functools
from redis import StrictRedis, ConnectionPool, Redis
import os


def init_redis_facility(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        redis_db_url = os.environ.get('REDIS_URL', None)
        if redis_db_url:
            self.redis = StrictRedis.from_url(redis_db_url)
        else:
            pool = ConnectionPool()
            self.redis = Redis(connection_pool=pool)
        return method(self, *args, **kwargs)
    return wrapper
