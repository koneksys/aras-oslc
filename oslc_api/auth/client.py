import json
import logging
from http.client import UNAUTHORIZED

import requests
from flask_restx import abort
from urllib3.exceptions import MaxRetryError
from werkzeug.exceptions import BadRequest, InternalServerError

from oslc_api.auth.exceptions import OAuthError
from oslc_api.auth.models import User

logger = logging.getLogger(__name__)

ARAS_API_PARAMS = (
    'grant_type',
    'scope',
    'client_id',
    'username',
    'password',
    'database',
)


class ArasAPI:
    __instance = None
    __aras_base_api_uri = None
    __aras_server_uri = None
    __aras_discovery_api_uri = None
    __aras_openid_configuration = None
    __aras_token_endpoint_uri = None
    __aras_end_session_endpoint_uri = None

    __grant_type = 'password'
    __scope = None
    __client_id = None
    __username = None
    __password = None
    __database = None
    __token = None
    __user = None

    __source_base_uri = None

    @property
    def source_base_uri(self):
        return self.__source_base_uri

    @property
    def token(self):
        return self.__token

    @token.setter
    def token(self, token):
        self.__token = token

    @property
    def user(self):
        return self.__user

    @user.setter
    def user(self, user):
        self.__user = user

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(ArasAPI, cls).__new__(cls, *args, **kwargs)

        return cls.__instance

    def __init__(self, app=None):
        super(ArasAPI, self).__init__()
        self.app = app

    def init_app(self, app, aras_base_api_uri, scope, client_id, database):
        logger.debug('Initializing the ARAS API client.')
        self.app = app
        self.__aras_base_api_uri = aras_base_api_uri
        self.__scope = scope
        self.__client_id = client_id
        self.__database = database

        self.__source_base_uri = self.__aras_base_api_uri.rstrip('/') + '/server/odata/'

    def __get(self, url: str, headers: dict = None, data: dict = None):

        try:
            if not headers:
                res = requests.get(url)
            else:
                if not data:
                    res = requests.get(url, headers=headers)
                else:
                    res = requests.get(url, headers=headers, data=data)

            if not res:
                description = res.content.decode('utf-8')

                if res.status_code == UNAUTHORIZED:
                    abort(code=UNAUTHORIZED)

                raise BadRequest(description if description else None)

            return res
        except requests.exceptions.ConnectionError as e:
            if isinstance(e.args[0], MaxRetryError):
                logger.debug(f'MaxRetryError when connection to: {url}')
                raise e
            else:
                raise InternalServerError(e.args[0].args[0])

    def __post(self, url: str, payload: dict = None):

        try:
            res = requests.post(url, data=payload)
            if not res:
                content = res.content.decode('utf-8')
                raise BadRequest(json.loads(content)['error_description'] if content else None)

            return res
        except requests.exceptions.ConnectionError as e:
            if isinstance(e.args[0], MaxRetryError):
                raise e
            else:
                raise InternalServerError(e.args[0].args[0])

    def __get_server_url(self):
        self.__aras_discovery_api_uri = f'{self.__aras_base_api_uri}/Server/OAuthServerDiscovery.aspx'

        res = self.__get(self.__aras_discovery_api_uri)
        if res:
            locations = res.json()['locations']
            if len(locations) == 1:
                return locations[0]['uri']
            else:
                for location in locations:
                    if self.__aras_base_api_uri in location['uri']:
                        return location

        return None

    def __get_openid_configuration(self):
        if not self.__aras_server_uri:
            self.__aras_server_uri = self.__get_server_url()

        self.__token_endpoint_url = f'{self.__aras_server_uri}.well-known/openid-configuration'

        res = self.__get(self.__token_endpoint_url)
        if res:
            self.__aras_openid_configuration = res.json()

            return self.__aras_openid_configuration

        return None

    def __get_token_endpoint_uri(self):
        if not self.__aras_openid_configuration:
            self.__aras_openid_configuration = self.__get_openid_configuration()

        if 'token_endpoint' in self.__aras_openid_configuration:
            return self.__aras_openid_configuration.get('token_endpoint', None)

        return None

    def __get_end_session_endpoint_uri(self):
        if not self.__aras_openid_configuration:
            self.__aras_openid_configuration = self.__get_openid_configuration()

        if 'end_session_endpoint' in self.__aras_openid_configuration:
            return self.__aras_openid_configuration.get('end_session_endpoint', None)

        return None

    def __payload(self, username, password):
        return {
            'grant_type': self.__grant_type,
            'scope': self.__scope,
            'client_id': self.__client_id,
            'username': username,
            'password': password,
            'database': self.__database,
        }

    def get_token(self, username: str, password: str) -> str:

        if not self.__aras_token_endpoint_uri:
            self.__aras_token_endpoint_uri = self.__get_token_endpoint_uri()

        try:
            payload = self.__payload(username, password)
            token = self.__post(self.__aras_token_endpoint_uri, payload=payload)
            if token:
                self.__token = token.json()
                user = User(username=username, access_token=self.__token['access_token'])
                self.__user = user

            return self.__token
        except InternalServerError as e:
            raise BadRequest(e.description)

    def get_resource(self, url, data: dict = None):
        try:
            logger.debug(f'Requesting: {url}')
            headers = {
                "Authorization": "Bearer " + self.__token['access_token'],
                "Accept": "application/json"
            }
            res = self.__get(url, headers, data)
        except requests.exceptions.ConnectionError as e:
            raise e
        except InternalServerError as e:
            raise InternalServerError(e.description)

        return res

    def end_session(self):
        if not self.__aras_end_session_endpoint_uri:
            self.__aras_end_session_endpoint_uri = self.__get_end_session_endpoint_uri()

        try:
            res = self.__get(self.__aras_end_session_endpoint_uri)
            return res
        except OAuthError as e:
            raise BadRequest(e.description)
