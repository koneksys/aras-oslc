import logging

from oslc_api.aras.resources import OSLCResource


logger = logging.getLogger(__name__)


def test_singleton_instance():
    ins1 = OSLCResource()
    ins2 = OSLCResource()

    logger.debug(f'instance 1: {ins1}')
    logger.debug(f'instance 2: {ins2}')

    assert ins1 == ins2, 'The singleton is creating different instances'


def test_get_service_provider(source_base_uri, access_token,
                              mocker, load_item_types_test):

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

    resource = OSLCResource(source_base_uri=source_base_uri, access_token=access_token)
    sp = resource.get_service_provider('http://127.0.0.1:5000/')

    assert sp is not None, 'The request was not processed'

    g = sp.graph.serialize()

    assert b'ServiceProvider' in g, 'The Service Provider was not generated correctly'
    assert b'<rdf:type rdf:resource="http://open-services.net/ns/core#QueryCapability"/>' in g, 'The QC was not generated correctly'
    assert b'<rdf:type rdf:resource="http://open-services.net/ns/core#Service"/>' in g, 'The response does not contain a Service'


def test_get_query_capabilities(source_base_uri, access_token, item_values,
                                mocker, load_item_types_test, load_items_test):
    item_type = item_values[0]
    url = f'http://127.0.0.1:5000/api/oslc/{item_type}'
    url_sp = 'http://127.0.0.1:5000/api/oslc'
    # rs = f'<rdf:type rdf:resource="http://127.0.0.1:5000/api/oslc/{item_type}/resourceShape#"/>'

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_items',
            return_value=load_items_test
        )

    resource = OSLCResource(source_base_uri=source_base_uri, access_token=access_token)
    qc = resource.get_query_capabilities(item_type, url, url_sp)

    assert qc is not None, 'The request was not processed'

    g = qc.graph.serialize()

    assert len(qc.graph) >= 1, 'The graph is empty'
    # assert rs.encode('ascii') in g, 'The resource shape was not generated'
    assert b'rdfs:member rdf:resource' in g, 'The members were not generated'


def test_get_query_resource(source_base_uri, access_token, item_values,
                            mocker, load_item_types_test, load_items_test,
                            load_validate_configs_test, load_resource_shape_test,
                            load_query_expanded_item_test):
    item_type = item_values[0]
    config_id = item_values[1]
    url = f'http://127.0.0.1:5000/api/oslc/{item_type}/{config_id}'

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.validate_config_id',
            return_value=load_validate_configs_test
        )

        mocker.patch(
            'oslc_api.rest_api.aras.load_resource_shape',
            return_value=load_resource_shape_test
        )

        mocker.patch(
            'oslc_api.rest_api.aras.get_resource_shape',
            return_value=None
        )

        mocker.patch(
            'oslc_api.rest_api.aras.query_expanded_item',
            return_value=load_query_expanded_item_test
        )

        mocker.patch(
            'oslc_api.rest_api.aras.check_if_versionable',
            return_value=True
        )

        mocker.patch(
            'oslc_api.rest_api.aras.query_relation_properties',
            return_value=load_query_expanded_item_test
        )

    resource = OSLCResource(source_base_uri=source_base_uri, access_token=access_token)
    r = resource.get_query_resource(item_type, config_id, url, 'http://127.0.0.1:5000/api/oslc')

    assert r is not None, 'The request was not processed'
    assert len(r.graph) >= 1, 'The graph is empty'


def test_get_components(source_base_uri, access_token, item_values,
                        mocker, load_item_types_test, load_items_test):
    item_type = item_values[0]
    url = f'http://127.0.0.1:5000/api/oslc/{item_type}'

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.load_item_types',
            return_value=load_item_types_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_items',
            return_value=load_items_test
        )

    resource = OSLCResource(source_base_uri, access_token)
    comps = resource.get_components(item_type, url)

    assert comps is not None, 'The request was not processed'

    g = comps.graph.serialize()

    assert item_type.encode('ascii') in g, f'The {item_type} was not found in the response'


def test_get_component(source_base_uri, access_token, item_values,
                       mocker, load_validate_configs_test):
    item_type = item_values[0]
    config_id = item_values[1]
    url = f'http://127.0.0.1:5000/api/oslc/{item_type}/{config_id}'

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.validate_config_id',
            return_value=load_validate_configs_test
        )

    resource = OSLCResource(source_base_uri=source_base_uri, access_token=access_token)
    comp = resource.get_component(item_type, config_id, url)

    assert comp is not None, 'The request was not processed'

    g = comp.graph.serialize()

    assert item_type.encode('ascii') in g, f'The {item_type} was not found in the response'
    assert config_id.encode('ascii') in g, f'The {config_id} was not found in the response'


def test_get_configurations(source_base_uri, access_token, item_values,
                            mocker, load_validate_configs_test):

    item_type = item_values[0]
    config_id = item_values[1]
    url = f'http://127.0.0.1:5000/api/oslc/{item_type}/{config_id}/configurations'

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.validate_config_id',
            return_value=load_validate_configs_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_streams',
            return_value=load_validate_configs_test
        )

    resource = OSLCResource(source_base_uri=source_base_uri, access_token=access_token)
    configs = resource.get_configurations(item_type, config_id, url)

    assert configs is not None, 'The request was not processed'

    g = configs.graph.serialize()

    assert item_type.encode('ascii') in g, f'The {item_type} was not found in the response'
    assert config_id.encode('ascii') in g, f'The {config_id} was not found in the response'


def test_get_streams(source_base_uri, access_token, item_values, mocker, load_validate_configs_test):
    item_type = item_values[0]
    config_id = item_values[1]
    stream_id = item_values[2]

    if 'localhost' in source_base_uri:
        mocker.patch(
            'oslc_api.aras.resources.validate_config_id',
            return_value=load_validate_configs_test
        )

        mocker.patch(
            'oslc_api.aras.resources.load_streams',
            return_value={e['id']: e for e in load_validate_configs_test['value']}
        )

    url = f'http://127.0.0.1:5000/api/oslc/{item_type}/{config_id}/stream/{stream_id}'

    resource = OSLCResource(source_base_uri=source_base_uri, access_token=access_token)
    stream = resource.get_stream(item_type, config_id, stream_id, url)

    assert stream is not None, 'The request was not processed'

    g = stream.graph.serialize()

    assert item_type.encode('ascii') in g, 'The response does not contain the item type'
    assert config_id.encode('ascii') in g, 'The response does not contain the component'
    assert stream_id.encode('ascii') in g, 'The response does not contain the stream'
