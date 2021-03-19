import logging
import os
import re
from urllib.parse import quote, unquote

import rdflib
from rdflib import Graph, RDF, RDFS, DCTERMS, XSD, URIRef, Literal
from rdflib.resource import Resource

from oslc_api.aras.client import query_expanded_item, query_relation_properties, \
    query_item_types_list, query_item_instances, query_item_type_properties, query_item_type_relationships, \
    query_item_generations, get_is_versionable, get_current_item_id, get_validate_item_id, \
    get_validate_config_id
from oslc_api.aras.data import load_from_json_file
from oslc_api.aras.namespaces import ARAS, OSLC, OSLC_CONFIG
from oslc_api.aras.properties import RDFProperty

logger = logging.getLogger(__name__)


def load_item_types(source_base_uri: str) -> dict:
    item_types = dict()

    response = query_item_types_list(source_base_uri)

    if response and response.status_code == 200:
        data = response.json()

        if data:
            for p in data['value']:
                item_type_id = p['@odata.id'].replace('ItemType(\'', '').replace('\')', '')
                item_types[item_type_id] = p['name']

    return item_types


def get_item_rdf(item_graph: Graph, item_type: str, source_base_url: str, item_id: str, config_id: str, item_url: str,
                 url_sp: str):
    # Decode the item_url and replace whitespace with dot
    item_url = unquote(item_url)
    item_url = re.sub(' ', '.', item_url)

    # Get the resource shape graph to extract the relationships to be queried
    g = load_resource_shape(item_type, url_sp=url_sp,
                            source_base_url=source_base_url)
    if not g:
        return None

    rs = get_resource_shape(item_type, url_sp, source_base_url)
    if not rs:
        if g:
            rs = g
        else:
            return None

    oslc_base = url_sp
    oslc_resource_shape_base = oslc_base + '/' + re.sub(' ', '.', item_type) + "/resourceShape#"
    oslc_config_base = oslc_base + '/config'

    # Get expanded item JSON from the API by following the resource shapes file
    item_response = query_expanded_item(source_base_url, item_type, item_id, config_id, rs)
    if item_response:
        item_json = item_response.json()

    # equalize query responses to avoid having errors when the item_id was
    # inexistent and the config_id was used as filtering
    if 'value' in item_json.keys():
        item_json = item_json['value'][0]

    # set the item_id property if it wasn't passed in the method
    if not item_id:
        item_id = item_json['id']

    # Build RDF Graph for an item
    item_graph.bind('rdf', RDF)
    item_graph.bind('rdfs', RDFS)
    item_graph.bind('dcterms', DCTERMS)
    item_graph.bind('xsd', XSD)
    item_graph.bind('aras', ARAS)
    item_graph.bind('aras_' + re.sub(' ', '.', item_type), oslc_resource_shape_base)
    item_graph.bind('oslc', OSLC)
    item_graph.bind('oslc_config', OSLC_CONFIG)

    # Create the RDF resource shape node for each item type
    item_node = Resource(item_graph, URIRef(item_url))
    item_node.add(RDF.type, URIRef(ARAS + re.sub(' ', '.', item_type)))
    item_node.add(OSLC_CONFIG.component,
                  URIRef(oslc_config_base + '/' + re.sub(' ', '.', item_type) + '/component/' + config_id))
    item_node.add(OSLC.instanceShape, URIRef(oslc_resource_shape_base))

    # If the item is versionable, add version properties
    if check_if_versionable(source_base_url, item_type):
        item_node.add(RDF.type, URIRef(OSLC_CONFIG.VersionResource))
        item_node.add(OSLC_CONFIG.versionId, Literal(item_json.get('id'), datatype=XSD.string))
        item_node.add(DCTERMS.isVersionOf, URIRef(item_url))

    # Query and iterate through the item type properties to build the item graph
    qres = rs.query(
        """
        SELECT ?prop ?type ?def
            WHERE {
                ?s oslc:name ?prop.
                ?s oslc:occurs ?occurs.
                FILTER(?occurs IN (oslc:Exactly-one, oslc:Zero-or-one))
                OPTIONAL {
                    ?s ?type ?def.
                    FILTER(?type IN (oslc:valueType, oslc:propertyDefinition))
                }
            }
        """
    )

    # Iterate through the properties and insert them into the item graph
    for row in qres:
        # Extract the SPARQL results as the property name, data type, and property definitions
        prop = row['prop']
        data_type = row['type']
        resource_def = row['def']

        # iterate through the properties of the resource shapes file and get their value from the JSON response
        prop_val = None
        if item_json.get(str(prop)):
            prop_val = item_json.get(str(prop))

        if type(prop_val) is dict:
            prop_val = prop_val['config_id']['id']

        # Associate the property to the graph according to their data type/relationship
        if data_type == OSLC.propertyDefinition:
            prop_item_search = re.search('(.*?)api/oslc/(.*?)/resourceShape', resource_def, re.IGNORECASE)
            if prop_item_search:
                prop_item_type = prop_item_search.group(2)
                if prop_val:
                    logger.debug(f'property: {str(prop)}')
                    unquoted_pre = oslc_resource_shape_base + re.sub(' ', '.', prop)
                    unquoted_obj = oslc_base + '/' + re.sub(' ', '.', prop_item_type) + '/' + prop_val
                    unquoted_obj += '?oslc_config.context='
                    unquoted_obj += quote(oslc_config_base + '/' +
                                          re.sub(' ', '.', prop_item_type) +
                                          '/component/' +
                                          prop_val + '/stream/' + item_json[str(prop)]['id'])
                    item_node.add(URIRef(unquoted_pre), URIRef(unquoted_obj))
        elif data_type == OSLC.valueType:
            if prop_val:
                item_node.add(URIRef(oslc_resource_shape_base + re.sub(' ', '.', prop)),
                              Literal(prop_val, datatype=resource_def))

    # Iterate through the Zero-or-many properties and query for the external relationships
    qres = rs.query(
        """SELECT ?prop ?def
           WHERE {
              ?s oslc:name ?prop.
              ?s oslc:occurs oslc:Zero-or-many.
              ?s oslc:propertyDefinition ?def.
           }""")

    # Iterate through the properties and query the API to create a list of instances and insert into the
    #  item graph
    for row in qres:
        # Associate the SPARQL query results to variables
        rel_prop = str(row['prop'])
        rel_def = row['def']

        if str(rel_prop) not in ('oslc_component', 'oslc_version_id', 'dcterms_is_version_of'):
            rel_item_response = query_relation_properties(source_base_url, rel_prop, item_id)
            rel_item_json = None
            if rel_item_response:
                rel_item_json = rel_item_response.json()

            if rel_item_json is not None and rel_item_json.get('value'):
                for rel_item in rel_item_json.get('value'):
                    rel_prop_val = rel_item['config_id']['id']
                    prop_item_search = re.search('(.*?)api/oslc/(.*?)/resourceShape', rel_def, re.IGNORECASE)
                    if prop_item_search:
                        prop_item_type = prop_item_search.group(2)
                        if rel_prop_val:
                            unquoted_pre = oslc_resource_shape_base + re.sub(' ', '.', rel_prop)
                            unquoted_obj = oslc_base + '/' + re.sub(' ', '.', prop_item_type) + '/' + rel_prop_val
                            unquoted_obj += '?oslc_config.context='
                            unquoted_obj += quote(oslc_config_base + '/' +
                                                  re.sub(' ', '.', prop_item_type) + '/component/' +
                                                  rel_prop_val + '/stream/' + rel_item['id'])
                            item_node.add(URIRef(unquoted_pre),
                                          URIRef(unquoted_obj))

    return item_node


def load_items_json(item_type: str) -> dict:
    file = os.path.join('data', item_type + '_Items.json')
    data = load_from_json_file(file_name=file)

    return data


def load_items(source_base_uri: str, item_type: str,
               page_size: int = None, page_no: int = 0) -> dict:
    items = dict()

    page_no = page_no if page_no else 1
    response = query_item_instances(source_base_uri, item_type, page_size, page_no)

    if response and response.status_code == 200:
        data = response.json()

        if data:
            for item in data['value']:
                if 'config_id' in item:
                    item_id = item['config_id']['id']
                else:
                    item_id = item['id']

                items[item_id] = item

    return items


def load_item_versions_ids(source_base_uri: str, item_type: str, config_id: str) -> dict:
    response = query_item_generations(source_base_uri, item_type, config_id)

    if response and response.status_code == 200:
        data = response.json()
        return data


def load_streams(source_base_uri: str, item_type: str, config_id: str) -> dict:
    data = load_item_versions_ids(source_base_uri, item_type, config_id)

    s = {e['id']: e for e in data['value']}

    return s


def load_resource_shape(item_type: str,
                        url_sp: str = None,
                        source_base_url: str = None):
    g = get_resource_shape(item_type, url_sp, source_base_url)

    if g:
        if len(g):
            return g
        else:
            return None

    return g


def get_resource_shape(item_type: str, url_sp: str, source_base_url: str):
    # API base endpoints & credentials

    # OSLC API Base URL
    oslc_base = url_sp
    oslc_resource_shape_base = oslc_base + '/' + re.sub(' ', '.', item_type) + "/resourceShape"

    properties_response = query_item_type_properties(source_base_url, item_type)
    if properties_response and properties_response.json()['value'] and properties_response.status_code == 200:
        properties_json = properties_response.json()
    else:
        return None

    # Create a list of properties associated with the Iterated ItemType
    item_type_properties = list()

    # For each Property returned, save its name
    for value in properties_json['value']:
        # Register the property instance
        item_type_properties.append(
            RDFProperty(value['name'], value['data_type'],
                        value.get('data_source@aras.name', ''), value['is_required']))

    relationships_json = query_item_type_relationships(source_base_url, item_type).json()
    # Create a list of relationships associated with the Iterated ItemType
    item_type_relationships = list()

    # For each Relationship returned, save its name
    for value in relationships_json['value']:
        # Register the relationship instance
        item_type_relationships.append(value['name'])

    # Create an RDF graph using rdflib and associate the RDF schemas
    graph = rdflib.Graph()
    graph.bind('rdf', RDF)
    graph.bind('rdfs', RDFS)
    graph.bind('dcterms', DCTERMS)
    graph.bind('xsd', XSD)
    graph.bind('aras', ARAS)
    graph.bind('oslc', OSLC)
    graph.bind('oslc_config', OSLC_CONFIG)

    # Create the RDF resource shape node for each item type
    item_type_node_rdf = URIRef(
        oslc_resource_shape_base)
    graph.add((item_type_node_rdf, RDF.type, OSLC.ResourceShape))
    graph.add((item_type_node_rdf, DCTERMS.title, Literal(item_type)))
    graph.add((item_type_node_rdf, OSLC.describes, ARAS.ItemType))

    # Add oslc config properties
    # OSLC Component
    property_node_rdf = URIRef(item_type_node_rdf + "#oslc_component")
    graph.add((property_node_rdf, RDF.type, OSLC.Property))
    graph.add((property_node_rdf, OSLC.name, Literal('oslc_component')))
    graph.add((property_node_rdf, OSLC.occurs, URIRef(OSLC + "Zero-or-one")))
    graph.add((property_node_rdf, OSLC.range, URIRef(OSLC_CONFIG.component)))
    graph.add((property_node_rdf, OSLC.propertyDefinition, URIRef(OSLC_CONFIG.component)))
    graph.add((item_type_node_rdf, OSLC.property,
               property_node_rdf))

    # Add versioning properties if the item is versionable
    if check_if_versionable(source_base_url, item_type):
        # OSLC versionId
        property_node_rdf = URIRef(item_type_node_rdf + "#oslc_version_id")
        graph.add((property_node_rdf, RDF.type, OSLC.Property))
        graph.add((property_node_rdf, OSLC.name, Literal('oslc_version_id')))
        graph.add((property_node_rdf, OSLC.occurs, URIRef(OSLC + "Zero-or-many")))
        graph.add((property_node_rdf, OSLC.propertyDefinition, URIRef(OSLC_CONFIG.versionId)))
        graph.add((property_node_rdf, OSLC.valueType,
                   XSD.string))
        graph.add((item_type_node_rdf, OSLC.property,
                   property_node_rdf))

        # DCTERMS isVersionOf
        property_node_rdf = URIRef(item_type_node_rdf + "#dcterms_is_version_of")
        graph.add((property_node_rdf, RDF.type, OSLC.Property))
        graph.add((property_node_rdf, OSLC.name, Literal('dcterms_is_version_of')))
        graph.add((property_node_rdf, OSLC.occurs, URIRef(OSLC + "Exactly_one")))
        graph.add((property_node_rdf, OSLC.propertyDefinition, URIRef(DCTERMS.isVersionOf)))
        graph.add((item_type_node_rdf, OSLC.property,
                   property_node_rdf))

    # Add Properties and relate them to the given item type
    for item_property in item_type_properties:
        property_node_rdf = URIRef(item_type_node_rdf + "#" + re.sub(' ', '.', item_property.name))
        graph.add((property_node_rdf, RDF.type, OSLC.Property))
        graph.add((property_node_rdf, OSLC.name, Literal(item_property.name)))

        # Set OSLC occurs property based on if the property is required or not
        if item_property.required == "1":
            graph.add((property_node_rdf, OSLC.occurs, URIRef(OSLC + "Exactly-one")))
        else:
            graph.add((property_node_rdf, OSLC.occurs, URIRef(OSLC + "Zero-or-one")))

        # Alter ID property to refer to it's correct datatype as string
        if item_property.name == 'id':
            item_property.dataType = 'string'

        # Set property definition or data type
        if item_property.dataSource != '' and item_property.dataType == 'item':
            graph.add((property_node_rdf, OSLC.propertyDefinition,
                       URIRef(oslc_base + '/' + re.sub(' ', '.', item_property.dataSource) + "/resourceShape")))
        elif item_property.dataType == 'string' or item_property.dataType == 'text':
            graph.add((property_node_rdf, OSLC.valueType,
                       XSD.string))
        elif item_property.dataType == 'integer':
            graph.add((property_node_rdf, OSLC.valueType,
                       XSD.integer))
        elif item_property.dataType == 'float':
            graph.add((property_node_rdf, OSLC.valueType,
                       XSD.float))
        elif item_property.dataType == 'boolean':
            graph.add((property_node_rdf, OSLC.valueType,
                       XSD.boolean))
        elif item_property.dataType == 'date':
            graph.add((property_node_rdf, OSLC.valueType,
                       XSD.datetime))
        elif item_property.dataType == 'decimal':
            graph.add((property_node_rdf, OSLC.valueType,
                       XSD.decimal))
        else:
            # Mark all unrecognized types as string
            graph.add((property_node_rdf, OSLC.valueType,
                       XSD.string))
        graph.add((item_type_node_rdf, OSLC.property,
                   property_node_rdf))

    # Add Relationships to the given ItemType instance
    for rel in item_type_relationships:
        # Make sure that the ItemType being referenced exists
        property_node_rdf = URIRef(oslc_resource_shape_base + "#" + re.sub(' ', '.', rel))
        graph.add((property_node_rdf, RDF.type, OSLC.Property))
        graph.add((property_node_rdf, OSLC.name, Literal(rel)))
        graph.add((property_node_rdf, OSLC.propertyDefinition,
                   URIRef(oslc_base + '/' + re.sub(' ', '.', rel) + "/resourceShape")))
        graph.add((property_node_rdf, OSLC.occurs, URIRef(OSLC + "Zero-or-many")))
        graph.add((item_type_node_rdf, OSLC.property,
                   property_node_rdf))

    return graph


def check_if_versionable(source_base_url: str, item_type: str):
    request = get_is_versionable(source_base_url, item_type)

    data = request.json()
    for item in data['value']:
        is_versionable = item['is_versionable']

        if is_versionable == '1':
            return True
        else:
            return False


def query_current_item_id(source_base_url: str, item_type: str, config_id: str):
    request = get_current_item_id(source_base_url, item_type, config_id)

    data = request.json()
    for item in data['value']:
        is_current = item['is_current']

        if is_current == '1':
            return item['id']
        else:
            return False


def validate_item_id(source_base_url: str, item_type: str, item_id: str):
    request = get_validate_item_id(source_base_url, item_type, item_id)

    data = request.json()
    if request.status_code == 200:
        return data
    else:
        return False


def validate_config_id(source_base_url: str, item_type: str, config_id: str):
    request = get_validate_config_id(source_base_url, item_type, config_id)

    data = request.json()
    if len(data['value']):
        return data
    else:
        return False
