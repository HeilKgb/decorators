#!/usr/bin/env python3


import functools
from json import loads


def prepare_json(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.client_ip = self.request.headers.get("X-Real-IP") or self.request.remote_ip
        self.input_data = dict()
        if self.request.method in ['POST', 'PUT']:
            try:
                if self.request.headers["Content-Type"].startswith(
                        "application/json") and self.request.body:
                    self.input_data = loads(self.request.body.decode("utf-8"))
                for k, v in self.request.arguments.items():
                    try:
                        self.input_data[k] = v[0].decode("utf-8")
                    except:
                        self.input_data[k] = v[0].decode("utf-8", errors='ignore')
            except:
                return self.response(
                    400, 'Fail to parse input data. It must be sent ' +
                    'with header Content-Type: application/json and ' +
                    'JSON serialized.')
        return method(self, *args, **kwargs)
    return wrapper
