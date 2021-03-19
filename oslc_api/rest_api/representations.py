from http.client import OK

from flask import make_response, request
from rdflib import Graph, Literal, URIRef, RDF
from rdflib.resource import Resource

from oslc_api.aras.namespaces import OSLC

representations = {
    'json-ld': ['application/json', 'application/json+ld'],
    'turtle': ['text/turtle'],
    'pretty-xml': ['*/*', 'application/xml', 'application/rdf+xml']
}


def get_content_type(accept: str) -> str:
    content_type = 'json-ld'
    for key in representations.keys():
        if accept in representations[key]:
            content_type = key
            break

    return content_type


def output_rdf(data, code, headers=None):
    """Makes a Flask response with a JSON encoded body"""

    content_type = request.headers.get('accept')
    representation = get_content_type(content_type)

    if code == OK:
        data = data.to_rdf(representation)
    else:
        g = Graph()
        g.bind('oslc', OSLC)

        rsrc = Resource(g, URIRef(request.base_url))
        rsrc.add(RDF.type, OSLC.Error)

        if isinstance(data, dict):
            for attr in data:
                rsrc.add(OSLC.term(attr), Literal(data[attr]))

        data = g.serialize(format=representation)

    resp = make_response(data, code)
    resp.headers.extend(headers or {})

    return resp
