import logging

from oslc_api.auth import login
from oslc_api.auth.models import User

log = logging.getLogger(__name__)


def test_oslc_main(oslc_api, source_base_uri, access_token,
                   mocker, load_item_types_test):
    """
    GIVEN a Flask + RESTX (Swagger) application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

    response = oslc_api.get_service_provider(header={'X-ARAS-ACCESS-TOKEN': access_token})
    assert response is not None
    assert response.status_code == 200


def test_oslc_item_types(oslc_api, source_base_uri, access_token,
                         mocker, load_item_types_test):

    @login.request_loader
    def load_user_from_request(request):
        return User(username='admin', access_token=access_token)

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

    res = oslc_api.get_service_provider()
    assert res is not None
    assert res.status_code == 200, 'The request was not successful'
    assert b'ServiceProvider' in res.data, 'The response does not contain the ServiceProvider definition'


def test_oslc_items_by_item_type(oslc_api, source_base_uri, access_token, item_values,
                                 mocker, load_item_types_test, load_items_test):
    @login.request_loader
    def load_user_from_request(request):
        return User(username='admin', access_token=access_token)

    item_type = item_values[0]

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_items',
            return_value=load_items_test
        )

    res = oslc_api.get_query_capabilities(item_type)
    assert res is not None
    assert res.status_code == 200, 'The request was not successful'
    assert b'rdfs:member' in res.data, 'The response does not contain the ServiceProvider definition'


def test_oslc_item_by_item_type(oslc_api, source_base_uri, access_token, item_values,
                                mocker, load_item_types_test, load_items_test, load_validate_configs_test,
                                load_resource_shape_test, load_query_expanded_item_test):
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
            return_value={e['id']: e for e in load_validate_configs_test['value']}
        )

        mocker.patch(
            'oslc_api.rest_api.aras.load_resource_shape',
            return_value=load_resource_shape_test
        )

        mocker.patch(
            'oslc_api.rest_api.aras.query_expanded_item',
            return_value=load_query_expanded_item_test
        )

        mocker.patch(
            'oslc_api.rest_api.aras.get_resource_shape',
            return_value=None
        )

        mocker.patch(
            'oslc_api.rest_api.aras.check_if_versionable',
            return_value=True
        )

        mocker.patch(
            'oslc_api.rest_api.aras.query_relation_properties',
            return_value=load_query_expanded_item_test
        )

    res = oslc_api.get_query_resource(item_type, config_id)
    assert res is not None
    assert res.status_code == 200, 'The request was not successful'
    assert config_id.encode('ascii') in res.data, 'The response does not contain the config id'
