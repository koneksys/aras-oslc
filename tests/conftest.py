import json
import os
import time
from datetime import datetime, timezone

import pytest
import requests
from dotenv import load_dotenv
from rdflib import Graph
from urllib3.exceptions import MaxRetryError

from oslc_api import create_app
from oslc_api.auth import ArasAPI
from oslc_api.auth.models import User
from tests.functional.rest import OSLCAPI


@pytest.fixture(scope='session')
def app():
    """
    Initializing the Flask application for the OSLC API
    by passing the Config class as the configuration

    :return: app: Flask application
    """
    app = create_app('testing')
    app.testing = True
    yield app


@pytest.fixture(scope='session')
def client():
    """
    Getting the test_client instance for the Flask application
    for executing and validating the tests

    :param app: Flask application
    :return: client: Client with test configuration
    """
    # Create a test client using the Flask application configured for testing
    app = create_app('testing')
    app.testing = True
    with app.test_client() as client:
        # Establish an application context
        with app.app_context():
            yield client  # this is where the testing happens!

    # return app.test_client()


@pytest.fixture
def oslc_api(client):
    return OSLCAPI(client)


@pytest.fixture
def load_item_types_test() -> dict:
    item_types = dict()
    data = dict()
    file_name = 'data/sourceItemTypes.json'
    if os.path.isfile(file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)

        if data:
            for p in data['value']:
                item_type_id = p['@odata.id'].replace('ItemType(\'', '').replace('\')', '')
                item_types[item_type_id] = p['name']

    return item_types


@pytest.fixture
def load_items_test() -> dict:
    items = dict()
    file_name = 'data/Part_Items.json'
    if os.path.isfile(file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)

        if data:
            for item in data['value']:
                if 'config_id' in item:
                    item_id = item['config_id']['id']
                else:
                    item_id = item['id']

                items[item_id] = item

    return items


@pytest.fixture
def load_validate_configs_test() -> dict:
    file_name = 'data/Part_Items.json'
    if os.path.isfile(file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)

    return data


@pytest.fixture
def load_resource_shape_test():
    file_name = 'data/Part_ResourceShape.ttl'
    g = Graph()
    g.parse(file_name, format='turtle')
    return g


class Data(object):
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


@pytest.fixture
def load_query_expanded_item_test():
    file_name = 'data/Part_Extended.json'
    if os.path.isfile(file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)

    data = Data(data)
    return data


@pytest.fixture(scope='session')
def aras_api():
    aras_api = ArasAPI()

    base_dir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(base_dir, '.env'))

    client_id = 'IOMApp'
    aras_base_api_uri = os.environ.get('SOURCE_BASE_API_URI')
    aras_database = 'InnovatorSample'

    aras_api.init_app(None, aras_base_api_uri, 'Innovator', client_id, aras_database)

    utc_dt = datetime.now(timezone.utc)

    try:
        aras_api.get_token('admin', '607920b64fe136f9ab2389e371852af2')
    except requests.exceptions.ConnectionError as e:
        if isinstance(e.args[0], MaxRetryError):
            token = {
                'token_type': 'Bearer',
                'access_token': 'a',
                'refresh_token': 'b',
                'expires_in': '3600',
                'expires_at': int(time.time()) + 3600,
            }
            aras_api.token = token
            aras_api.user = User(username='admin', access_token=token['access_token'])

    return aras_api


@pytest.fixture(scope='session')
def source_base_uri(aras_api):
    return aras_api.source_base_uri


@pytest.fixture(scope='session')
def access_token(aras_api):
    return aras_api.token['access_token']


@pytest.fixture(scope='session')
def item_values(aras_api):
    if aras_api.token['access_token'] == 'a':
        item_type = 'Part'
        config_id = '5A456B42E6B34937BF8605C487220E67'
        item_id = '7E9058A7041540B4841A742B05DB741B'
    else:
        item_type = 'CAD'
        config_id = '61AB2C31D053445FB7C655E956C80AC9'
        item_id = '61AB2C31D053445FB7C655E956C80AC9'

    return item_type, config_id, item_id
