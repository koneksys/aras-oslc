import logging

from flask import make_response, request, g
from flask_login import LoginManager, user_loaded_from_request, user_loaded_from_header

from oslc_api.auth.client import ArasAPI
from oslc_api.rest_api.custom_session import CustomSessionInterface

logger = logging.getLogger(__name__)

aras_api = ArasAPI()
login = LoginManager()


@login.request_loader
def load_user_from_request(request):
    logger.debug('Looking for X-ARAS-ACCESS-TOKEN header')

    user = None
    access_token = request.headers.get('X-ARAS-ACCESS-TOKEN')
    if access_token:
        if aras_api.user and aras_api.user.access_token == access_token:
            user = aras_api.user

    logger.debug(f'X-ARAS-ACCESS-TOKEN: {user}')

    return user


@user_loaded_from_request.connect
def user_loaded_from_request(self, user=None):
    logger.debug(f'login_via_header: {True}')
    g.login_via_header = True


@user_loaded_from_header.connect
def user_loaded_from_header(self, user=None):
    logger.debug(f'login_via_header: {True}')
    g.login_via_header = True


@login.unauthorized_handler
def unauthorized():
    data = {
        'message': 'The resource is protected, you should authenticate to be able to access it'
    }
    logger.debug(f'Unauthenticated user <Request: {request.base_url}> : {data}')

    resp = make_response(data, 401)
    return resp


def init_app(app):
    client_id = app.config['OAUTH_CLIENT_ID']
    aras_base_api_uri = app.config['SOURCE_BASE_API_URI']
    aras_database = app.config['SOURCE_DATABASE']

    logger.debug("Initializing OAuth for: {}".format(client_id))

    login.init_app(app)

    aras_api.init_app(app, aras_base_api_uri, 'Innovator', client_id, aras_database)

    app.session_interface = CustomSessionInterface()
