import logging

from oslc_api.auth import login
from oslc_api.auth.models import User

log = logging.getLogger(__name__)


def test_components(oslc_api, source_base_uri, access_token, item_values,
                    mocker, load_item_types_test, load_items_test):
    @login.request_loader
    def load_user_from_request(request):
        return User(username='admin', access_token=access_token)

    item_type = item_values[0]
    config_id = item_values[1]

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_items',
            return_value=load_items_test
        )

    res = oslc_api.get_components(item_type)
    assert res is not None
    assert res.status_code == 200, 'The request was not successful'
    assert config_id.encode('ascii') in res.data, 'The response does not contain the config id'


def test_component(oslc_api, source_base_uri, access_token, item_values,
                   mocker, load_item_types_test, load_items_test, load_validate_configs_test):
    @login.request_loader
    def load_user_from_request(request):
        return User(username='admin', access_token=access_token)

    item_type = item_values[0]
    config_id = item_values[1]

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_items',
            return_value=load_items_test
        )

        mocker.patch(
            'oslc_api.aras.resources.validate_config_id',
            return_value=load_validate_configs_test
        )

    res = oslc_api.get_component(item_type, config_id)
    assert res is not None
    assert res.status_code == 200, 'The request was not successful'
    assert config_id.encode('ascii') in res.data, 'The response does not contain the config id'
    assert b'oslc_config:configurations' in res.data


def test_configurations(oslc_api, source_base_uri, access_token, item_values,
                        mocker, load_item_types_test, load_items_test, load_validate_configs_test,
                        load_resource_shape_test):
    @login.request_loader
    def load_user_from_request(request):
        return User(username='admin', access_token=access_token)

    item_type = item_values[0]
    config_id = item_values[1]

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_items',
            return_value=load_items_test
        )

        mocker.patch(
            'oslc_api.aras.resources.validate_config_id',
            return_value=load_resource_shape_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_streams',
            return_value=load_validate_configs_test
        )

    res = oslc_api.get_configurations(item_type, config_id)
    assert res is not None
    assert res.status_code == 200, 'The request was not successful'
    assert config_id.encode('ascii') in res.data, 'The response does not contain the config id'
    assert b'rdfs:member' in res.data
