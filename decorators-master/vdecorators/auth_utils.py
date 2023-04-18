#!/usr/bin/env python3

import os
import functools
from logging import info
from json import loads, dumps
from tornado.web import decode_signed_value
from tornado.gen import Task
from datetime import datetime
from urllib.parse import unquote
from vutils import token_decode
from dateutil.relativedelta import relativedelta


def https_required(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        using_ssl = (self.request.headers.get('X-Scheme', 'http') == 'https')
        if not using_ssl:
            self.response(403, 'A SSL (https) connection is required.')
            return
        info('HTTPS connection verified.')
        return method(self, *args, **kwargs)
    return wrapper


def vpc_access_only(handler_class):
    ''' Handle Tornado HTTP Basic Auth '''
    def wrap_execute(handler_execute):
        def require_cross(handler, kwargs):
            info('This is a VPC Request')
            # Force to accept requests only in the VPC
            remote_ip = handler.request.headers.get("X-Real-IP") or handler.request.remote_ip
            info('IP requesting VPC connection: ' + remote_ip)
            cross_token = str(handler.request.headers.get('Cross-Key', '123456'))
            info('Cross token: ' + str(cross_token))
            if 'CROSS_KEY' in handler.settings.keys():
                cross_key = handler.settings['CROSS_KEY']
                # Cross token lives for 10 minutes (10 * 0.0006945) considering same TZ
                check = token_decode(cross_token, cross_key)
                check = decode_signed_value(
                    cross_key, 'crosstoken',
                    check, max_age_days=0.006945)
                if check:
                    # Ok, here the key can live for 10 minutes.
                    info('The key was decoded, now check time.')
                    try:
                        if datetime.utcfromtimestamp(float(check)) + relativedelta(minutes=10) >= datetime.utcnow():
                            info('The key is valid.')
                            return True
                    except Exception as e:
                        info('Fail to convert cross token to be evaluated. {}'.format(e))
                info('The key is invalid.')
            else:
                info('Check the configuration for CROSS_KEY variable on settings.py file.')
            handler.set_status(401)
            handler._transforms = []
            handler.set_header('Content-Type', 'application/json; charset=UTF-8')
            handler.write('{"status": "unauthorized", "message": "This resource is available only to logged users."}')
            handler.finish()
            return False

        def _execute(self, transforms, *args, **kwargs):
            if not require_cross(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class


def api_authenticated(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if hasattr(self, 'token_passed_but_invalid'):
                self.response(401, 'Authentication credentials is invalid.')
            else:
                self.response(401, 'Authentication required.')
            return
        return method(self, *args, **kwargs)
    return wrapper


# def authcenter_authenticated(method):
#     """ This decorator authenticates internal services checking the token with
#         the auth-center service """
#     @functools.wraps(method)
#     def wrapper(self, *args, **kwargs):
#         info('>>>> Authentication required to access this resource')
#         self.current_user = None
#         # get the token for authentication
#         token = self.request.headers.get("Venidera-AuthToken")
#         if token:
#             token = unquote(token)
#             # Search for the token into RedisDB
#             authinfo = self.check_auth_token(token)
#             if authinfo:
#                 # Authenticated
#                 self.current_user = authinfo
#             else:
#                 try:
#                     # No token, so check with AUTHCENTER LOCAL
#                     body = {'token': token}
#                     url = self.settings['AUTHCENTER'] + '/auth/crosslogin'
#                     response = yield Task(
#                         self.http_call, url=url, method='POST', body=body, raw_response=False)
#                     if response['status_code'] == 200:
#                         # Valid VAT
#                         auth_user_info = response['data']['data']
#                         self.current_user = auth_user_info
#                         self.store_auth_token(token, auth_user_info)
#                     else:
#                         self.token_passed_but_invalid = True
#                 except Exception as e:
#                     info('Fail to access the auth-center: {}'.format(e))
#         info('>>> Authentiation check finished')
#         if not self.current_user:
#             info('Request not authenticated.')
#             if hasattr(self, 'token_passed_but_invalid'):
#                 self.response(401, 'Authentication credentials is invalid.')
#             else:
#                 self.response(401, 'Authentication required.')
#             return
#         else:
#             info('Request successfully authenticated.')
#         return method(self, *args, **kwargs)
#     return wrapper


def allowAdmin(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.current_user is None:
            self.response(401, 'Acesso querer autenticação.')
            return

        if self.current_user['role'] != 'Administrator':
            self.response(403, 'Acesso permitido somente aos administradores.')
            return

        return method(self, *args, **kwargs)
    return wrapper


def check_credentials(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        info('=============================================')
        info(' Authentication Process Started')
        info('---------------------------------------------')
        self.current_user = None
        self.VAT = None
        # Get config
        # # Check credentials expiration
        # if 'max_days_valid' in self.settings.keys():
        #     max_days_valid = self.settings['max_days_valid']
        # else:
        #     max_days_valid = 5
        # Authcenter crosslogin url
        # set the AUTHCENTER_LOCAL variable when located on the venidera's network
        url = os.environ.get(
            'AUTHCENTER_LOCAL', self.settings['AUTHCENTER']) + '/auth/crosslogin'
        # Get authentication credentials
        # Precedence:
        # 1 - Token (Header)
        # 2 - Cookie appkey + Cookie VAT (token)
        # 3 - VAT (token)
        try:
            token_header = unquote(self.request.headers.get("Venidera-AuthToken"))
        except Exception as e:
            info(e)
            token_header = None
        try:
            VAT = self.get_cookie("VAT")
            token_cookie = unquote(VAT)
        except Exception as e:
            token_cookie = None
        app_cookie = self.get_secure_cookie('appKey')
        if app_cookie:
            try:
                app_cookie = loads(app_cookie)
            except Exception as e:
                app_cookie = None
        # Credentials Loaded
        # Start check
        token_check = None
        if token_header or token_cookie:
            info('Check Token')
            body = self.json_encode({'token': token_header or token_cookie})
            response = yield Task(self.http_call, url=url, method='POST', body=body)
            if response.code == 200:
                # Usuário com VAT Válido
                token_check = loads(response.body.decode('utf-8'))['data']
            else:
                info('Token not valid... Autentication Failed')
        if token_check:
            # Header token authentication
            if token_header and (not token_cookie and not app_cookie):
                info('Authentication type: TOKEN (header)')
                self.current_user = token_check
                self.VAT = token_header
                info('... API Login OK!')
            # VAT token authentication
            elif token_cookie and not app_cookie:
                info('Authentication type: VAT (cookie) and no appkey')
                self.current_user = token_check
                self.VAT = token_cookie
                self.set_secure_cookie("appKey", dumps(self.current_user))
                info('... Login OK!')
            elif app_cookie and token_cookie:
                # Auth will be ok to this app
                info('Authentication type: COOKIE (appkey)')
                if app_cookie['username'] != token_check['username']:
                    self.current_user = token_check
                    self.set_secure_cookie("appKey", dumps(self.current_user))
                else:
                    self.current_user = app_cookie
                self.VAT = token_cookie
                info('... Login OK and Credentials Updated!')
        else:
            # Sem informação de login
            info('No credentials found.')
        info('---------------------------------------------')
        info(' Authentication Process Finished')
        info('=============================================')
        return method(self, *args, **kwargs)
    return wrapper
