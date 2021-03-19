import re
from urllib.parse import unquote

from rdflib import Graph

from oslc_api.auth import aras_api


def query_expanded_item(source_base_url: str, item_type: str,
                        item_id: str, config_id: str, resource_shapes_graph: Graph):
    # Build the query according to if the item_id was passed or not
    query_url = source_base_url + unquote(re.sub('\\.', ' ', item_type))
    if item_id:
        query_url += '(\'' + item_id + '\')'

    # Query and iterate through the direct relationships of an item and set the query_url to expand all of them
    qres = resource_shapes_graph.query(
        """SELECT ?prop
           WHERE {
              ?s oslc:name ?prop.
              ?s oslc:occurs ?occurs.
              ?s oslc:propertyDefinition ?def.
              FILTER(?occurs IN (oslc:Exactly-one, oslc:Zero-or-one))
           }""")

    if len(qres):
        query_url += '?$expand='

    i = 0
    for row in qres:
        # Remove OSLC Specific Properties
        prop = row['prop']
        if str(prop) != ('oslc_component' or 'oslc_version_id' or 'dcterms_is_version_of'):
            query_url += prop + '($expand=config_id)'
            if i != len(qres) - 1:
                query_url += ', '

        i += 1

    if not item_id:
        query_url += '&$filter=config_id eq \'' + config_id + '\''

    # Request Item from the API and save it as JSON
    item_request = aras_api.get_resource(query_url)

    return item_request


def query_relation_properties(source_base_url: str, prop: str, item_id: str):
    # Query the API to get the related items and then add them as OSLC properties for the item resource
    query = source_base_url + unquote(
        re.sub('\\.', ' ', prop)) + '?$filter=source_id/id eq \'' + item_id + '\'&$expand=config_id'

    item_request = aras_api.get_resource(query)

    return item_request


def query_item_types_list(source_base_url: str):
    # Request the Item Types from the API and save it as JSON

    item_types_request = aras_api.get_resource(source_base_url + 'ItemType?$select=name')

    return item_types_request


def query_item_instances(source_base_url: str, item_type: str, page_size=None, page_no=None):
    query_string = source_base_url + unquote(
        re.sub('\\.', ' ', item_type)) + '?$select=keyed_name, id&$expand=config_id'

    if page_size:
        query_string += '&$top=' + str(page_size)
        skip = page_size * (page_no - 1)
        query_string += '&$skip=' + str(skip)

    # Request the Item Instance from the API and save it as JSON

    items_request = aras_api.get_resource(query_string)

    return items_request


def query_item_generations(source_base_url: str, item_type: str, config_id: str):
    body = '{ \"config_id\" : \"' + config_id + '\" }'
    # Request the Item Instance from the API and save it as JSON

    items_request = aras_api.get_resource(source_base_url + unquote(re.sub('\\.', ' ',
                                                                            item_type)) +
                                          '?$select=keyed_name, id&$filter=generation gt \'0\'', data=body)

    return items_request


def query_item_type_properties(source_base_url: str, item_type: str):
    # Request the ItemTypes PROPERTIES from the API and save it as JSON

    properties_request = aras_api.get_resource(
        source_base_url + 'Property?$filter=source_id/name eq \'' + unquote(re.sub('\\.', ' ', item_type)) + '\'')

    return properties_request


def query_item_type_relationships(source_base_url: str, item_type: str):
    # Request the ItemTypes RelationshipType from the API and save it as JSON
    relationships_request = aras_api.get_resource(
        source_base_url + 'RelationshipType?$filter=source_id/name eq \'' + unquote(
            re.sub('\\.', ' ', item_type)) + '\'')

    return relationships_request


def get_is_versionable(source_base_url: str, item_type: str):
    request = aras_api.get_resource(
        source_base_url + 'ItemType?$filter=name eq \'' + unquote(re.sub('\\.', ' ', item_type)) + '\'' +
        '&$select=name, is_versionable')

    return request


def get_current_item_id(source_base_url: str, item_type: str, config_id: str):
    body = '{ \"config_id\" : \"' + config_id + '\" }'
    request = aras_api.get_resource(
        source_base_url + unquote(re.sub('\\.', ' ', item_type)) + '?$select=id, is_current', data=body)

    return request


def get_validate_item_id(source_base_url: str, item_type: str, item_id: str):
    request = aras_api.get_resource(
        source_base_url + unquote(re.sub('\\.', ' ', item_type)) + '(\'' + item_id + '\')?$select=id, keyed_name&$expand=config_id')

    return request


def get_validate_config_id(source_base_url: str, item_type: str, config_id: str):
    body = '{ \"config_id\" : \"' + config_id + '\" }'
    request = aras_api.get_resource(source_base_url + unquote(re.sub('\\.', ' ', item_type)) + '?$select=id, keyed_name', data=body)

    return request
