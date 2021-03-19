import logging

from oslc_api.rest_api.aras import load_item_types, load_items, load_resource_shape

logger = logging.getLogger(__name__)


def test_load_item_types(source_base_uri, mocker, load_item_types_test):
    """
    GIVEN the Flask app and the SOURCE_BASE_URI
    WHEN loading the item types
    THEN check that the Part, Product and CAD are available
    """

    if 'localhost' in source_base_uri:
        mocker.patch(
            'tests.unit.test_aras.load_item_types',
            return_value=load_item_types_test
        )

    data = load_item_types(source_base_uri)

    assert data is not None
    assert 'Part' in data.values()
    assert 'Product' in data.values()
    assert 'CAD' in data.values()


def test_load_items_by_item_type(source_base_uri, access_token, item_values, mocker, load_items_test):
    """
    GIVEN the Flask app and the SOURCE_BASE_URI
    WHEN loading the items for an item type
    THEN checking that the config_id is present on the response
    """
    item_type = item_values[0]
    config_id = item_values[1]

    if 'localhost' in source_base_uri:
        mocker.patch(
            'tests.unit.test_aras.load_items',
            return_value=load_items_test
        )

    data = load_items(source_base_uri, item_type)

    assert data is not None
    assert config_id in data.keys()


def test_load_resource_shape(source_base_uri, access_token, item_values, mocker, load_resource_shape_test):
    item_type = item_values[0]
    url_sp = 'http://127.0.0.1:5000/api/oslc'

    if 'localhost' in source_base_uri:
        mocker.patch(
            'tests.unit.test_aras.load_resource_shape',
            return_value=load_resource_shape_test
        )

    data = load_resource_shape(item_type, url_sp=url_sp, source_base_url=source_base_uri)

    assert data is not None
    assert len(data) >= 0
    assert b'<rdf:type rdf:resource="http://open-services.net/ns/core#ResourceShape"/>' in data.serialize()
