import logging
import re
from collections import OrderedDict
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse, unquote

from rdflib import Graph, DCTERMS, URIRef, RDF, BNode, Literal, RDFS
from rdflib.resource import Resource

from oslc_api.rest_api.aras import validate_item_id, validate_config_id
from oslc_api.aras.namespaces import OSLC, ARAS, OSLC_CONFIG, LDP
from oslc_api.rest_api.aras import load_item_types, load_items, load_resource_shape, get_item_rdf, \
    load_streams

logger = logging.getLogger(__name__)


class OSLCResource:
    __instance = None
    __graph = None
    __item_types = OrderedDict()

    __source_base_uri = None
    __access_token = None

    def __new__(cls, source_base_uri: str = None, access_token: str = None, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(OSLCResource, cls).__new__(cls, *args, **kwargs)
            cls.__init_graph()

            cls.__source_base_uri = source_base_uri
            cls.__access_token = access_token

        return cls.__instance

    @classmethod
    def __init_graph(cls):
        cls.__graph = Graph()
        cls.__graph.bind('oslc', OSLC)
        cls.__graph.bind('oslc_config', OSLC_CONFIG)
        cls.__graph.bind('aras', ARAS)
        cls.__graph.bind('dcterms', DCTERMS)
        cls.__graph.bind('ldp', LDP)

    @classmethod
    def get_service_provider(cls, url: str):
        if not cls.__instance:
            cls()

        cls.__init_graph()

        service_provider = None

        service = cls.__get_service(url=url)
        if service:
            service_provider = Resource(cls.__graph, URIRef(url))
            service_provider.add(RDF.type, OSLC.ServiceProvider)
            service_provider.add(OSLC.service, service)
            return service_provider
        else:
            return False

    @classmethod
    def get_query_capabilities(cls, item_type: str, url: str, url_sp: str,
                               paging: bool = False, page_size: int = 0, page_no: int = 1):
        if not cls.__instance:
            cls()

        cls.__init_graph()

        if not cls.__item_types:
            cls.__item_types = cls.__get_item_types()

        if re.sub('\\.', ' ', item_type) in cls.__item_types.values():
            item_type = re.sub(' ', '.', item_type)
            url = unquote(url)
            url = re.sub(' ', '.', url)
            logger.debug(f'{page_no}-{page_size}-{paging}')
            response_info = cls.__get_response_info(item_type, url, url_sp, paging, page_size, page_no)
            return response_info
        else:
            return False

    @classmethod
    def get_query_resource(cls, item_type: str, config_id: str, url: str, url_sp: str, config_context: str = None):
        if not cls.__instance:
            cls()

        cls.__init_graph()

        # If the config_context exists, extract the item_id and validate it + config_id
        if config_context:
            item_id = urlparse(config_context, allow_fragments=True).path.split('/')[-1]
            validated_config_id_from_item_id = validate_item_id(cls.__source_base_uri, item_type, item_id)
            if validated_config_id_from_item_id:
                val_config_id = validated_config_id_from_item_id['config_id']['id']
                if config_id == val_config_id:
                    resource = cls.__get_resource(item_type, item_id, config_id, url, url_sp)
                    return resource
                else:
                    return False
        # Else, only validate the conifg_id
        else:
            validated_config_id = validate_config_id(cls.__source_base_uri, item_type, config_id)
            if validated_config_id:
                resource = cls.__get_resource(item_type, None, config_id, url, url_sp)
                return resource
            else:
                return False

    @classmethod
    def get_resource_shape(cls, item_type: str, url: str, url_sp: str):
        if not cls.__instance:
            cls()

        cls.__init_graph()

        resource_shape = Resource(cls.__graph, URIRef(url))
        resource_shape.add(RDF.type, OSLC.ResourceShape)

        rs = cls.__get_resource_shape(item_type, url_sp, cls.__source_base_uri)

        if rs:
            for subject in rs.subjects(RDF.type, OSLC.Property):

                prop = Resource(cls.__graph, subject)
                prop.add(RDF.type, OSLC.Property)

                for p, o in rs.predicate_objects(subject):
                    prop.add(p, o)

                resource_shape.add(OSLC.property, prop)

            return resource_shape
        else:
            return False

    @classmethod
    def __get_service(cls, url: str) -> Resource:
        service = None
        cls.__item_types = cls.__get_item_types()

        if cls.__item_types:

            service = Resource(cls.__graph, BNode())
            service.add(RDF.type, OSLC.Service)
            service.add(OSLC.domain, URIRef(ARAS))

            qc_url = url + '/{itemType}'
            for item_type in cls.__item_types:
                item_type_name = cls.__item_types.get(item_type)
                item_type_name_url = re.sub(' ', '.', item_type_name)
                uri = urlparse(qc_url.format(**{'itemType': item_type_name_url}))
                qc = cls.__get_query_capability(item_type_name, item_type_name_url, uri.geturl())
                service.add(OSLC.queryCapability, qc)

        return service

    @classmethod
    def __get_query_capability(cls, item_type_name: str, item_type_name_url: str, uri: str) -> Resource:

        qc = Resource(cls.__graph, BNode())
        qc.add(RDF.type, OSLC.QueryCapability)
        qc.add(DCTERMS.title, Literal(f'Query Capability for ItemType: {item_type_name}'))
        qc.add(OSLC.queryBase, URIRef(uri))
        qc.add(OSLC.resourceType, URIRef(ARAS.term(item_type_name_url)))
        qc.add(OSLC.resourceShape, URIRef(uri + '/resourceShape'))

        return qc

    @classmethod
    def __get_response_info(cls, item_type: str, url: str, url_sp: str, paging: bool, page_size: int, page_no: int) -> Resource:

        items = load_items(cls.__source_base_uri, item_type, page_size, page_no)

        resource = Resource(cls.__graph, URIRef(url))
        ri, items = cls.__get_paging(item_type, items, url, paging, page_size, page_no)
        if ri:
            resource.add(OSLC.responseInfo, ri)

        for item in items:
            item_url = url + '/' + re.sub(' ', '.', item)
            member = Resource(cls.__graph, URIRef(item_url))
            resource.add(RDFS.member, member)

        return resource

    @classmethod
    def __get_resource(cls, item_type: str, item_id, config_id: str, url: str, url_sp: str) -> Resource:
        resource = get_item_rdf(cls.__graph, item_type,
                                cls.__source_base_uri,
                                item_id, config_id, url, url_sp)
        return resource

    @staticmethod
    def __get_resource_shape(item_type: str, url_sp: str, source_base_uri: str) -> Graph:
        return load_resource_shape(item_type, url_sp=url_sp,
                                   source_base_url=source_base_uri)

    @classmethod
    def __get_item_types(cls) -> dict:
        return load_item_types(cls.__source_base_uri)

    @classmethod
    def to_rdf(cls, representation: str = 'xml'):
        data = None
        if len(cls.__graph):
            data = cls.__graph.serialize(format=representation)
        return data

    @staticmethod
    def __get_url(url: str, params: dict) -> str:
        new_url = urlparse(url)
        query = dict(parse_qsl(new_url.query))
        query.update(params)

        query_string = urlencode(query)

        new_url = new_url._replace(query=query_string)

        return urlunparse(new_url)

    @classmethod
    def get_components(cls, item_type: str, url: str,
                       paging: bool = False, page_size: int = 0, page_no: int = 0):
        if not cls.__instance:
            cls()

        cls.__init_graph()

        if not cls.__item_types:
            cls.__item_types = cls.__get_item_types()

        if re.sub('\\.', ' ', item_type) in cls.__item_types.values():
            item_type = unquote(item_type)
            item_type = re.sub(' ', '.', item_type)
            url = unquote(url)
            url = re.sub(' ', '.', url)

            container = Resource(cls.__graph, URIRef(url))
            container.add(RDF.type, LDP.BasicContainer)

            config_ids = load_items(cls.__source_base_uri, item_type, page_size, page_no)

            ri, config_ids = cls.__get_paging(item_type, config_ids, url, paging, page_size, page_no)
            if ri:
                container.add(OSLC.responseInfo, ri)

            for config_id in config_ids:
                member_url = url + f'/{config_id}'
                member = Resource(cls.__graph, URIRef(member_url))
                member.add(RDF.type, OSLC_CONFIG.Component)
                member.add(DCTERMS.title, Literal(config_ids[config_id]['keyed_name']))

                container.add(LDP.contains, member)

            return container

        else:
            return False

    @classmethod
    def get_component(cls, item_type: str, config_id: str, url: str):
        if not cls.__instance:
            cls()

        cls.__init_graph()

        validated_item = validate_config_id(cls.__source_base_uri, item_type, config_id)

        if validated_item:
            item_type = unquote(item_type)
            item_type = re.sub(' ', '.', item_type)
            url = unquote(url)
            url = re.sub(' ', '.', url)

            component = Resource(cls.__graph, URIRef(url))
            component.add(RDF.type, OSLC_CONFIG.Component)

            keyed_name = None

            for item in validated_item['value']:
                keyed_name = item['keyed_name']

            if keyed_name:
                component.add(DCTERMS.title, Literal(keyed_name))

            component.add(OSLC_CONFIG.configurations, URIRef(url + '/configurations'))

            return component

        else:
            return False

    @classmethod
    def get_configurations(cls, item_type: str, config_id: str, url: str):
        if not cls.__instance:
            cls()

        cls.__init_graph()

        validated_item = validate_config_id(cls.__source_base_uri, item_type, config_id)

        if validated_item:
            item_type = unquote(item_type)
            item_type = re.sub(' ', '.', item_type)
            url = unquote(url)
            url = re.sub(' ', '.', url)

            container = Resource(cls.__graph, URIRef(url))

            streams = load_streams(cls.__source_base_uri, item_type, config_id)
            for stream in streams.keys():
                member = Resource(cls.__graph, URIRef(url.replace('configurations', 'stream') + f'/{stream}'))
                container.add(RDFS.member, member)

            return container

        else:
            return False

    @classmethod
    def get_stream(cls, item_type: str, config_id: str, stream_id: str, url: str):
        if not cls.__instance:
            cls()

        cls.__init_graph()

        validated_item = validate_config_id(cls.__source_base_uri, item_type, config_id)

        if validated_item:
            item_type = unquote(item_type)
            item_type = re.sub(' ', '.', item_type)
            url = unquote(url)
            url = re.sub(' ', '.', url)

            streams = load_streams(cls.__source_base_uri, item_type,
                                   config_id)
            if stream_id in streams.keys():
                stream = streams[stream_id]
                configuration = Resource(cls.__graph, URIRef(url))
                configuration.add(RDF.type, OSLC_CONFIG.Stream)
                configuration.add(DCTERMS.identifier, Literal(stream['id']))
                configuration.add(DCTERMS.title, Literal(stream['keyed_name']))

                return configuration
            else:
                return False
        else:
            return False

    @classmethod
    def __get_paging(cls, item_type: str, items: dict, url: str, paging: bool, page_size: int, page_no: int) -> tuple:
        ri = None
        paging = paging if paging else page_size > 0
        if paging:
            page_size = page_size if page_size else 50
            page_no = page_no if page_no else 1

            params = {'oslc.paging': 'true'}
            if page_size:
                params['oslc.pageSize'] = page_size

            if page_no:
                params['oslc.pageNo'] = page_no

            ri_url = cls.__get_url(url, params)

            ri = Resource(cls.__graph, URIRef(ri_url))
            ri.add(RDF.type, OSLC.ResponseInfo)

            ri.add(DCTERMS.title, Literal(f'Query Results for {item_type}'))

            params['oslc.pageNo'] = page_no + 1
            ri_url = cls.__get_url(url, params)
            ri.add(OSLC.nextPage, URIRef(ri_url))

        return ri, items
