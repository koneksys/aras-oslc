import logging
from http.client import UNAUTHORIZED

from flask import request, make_response, url_for, current_app
from flask_login import login_required, current_user
from flask_restx import Resource, Namespace
from werkzeug.exceptions import Unauthorized

from oslc_api.aras.resources import OSLCResource
from oslc_api.rest_api import api, authorizations
from oslc_api.rest_api.parsers import paging_parser, config_parser
from oslc_api.rest_api.representations import get_content_type

logger = logging.getLogger(__name__)

oslc_ns = Namespace('oslc', description='OSLC Adaptor', path='/api/oslc', authorizations=authorizations)


@oslc_ns.errorhandler(Unauthorized)
def handle_unauthorized_request(e):
    response = {
        "statusCode": e.code,
        "name": e.name,
        "message": e.description,
    }

    return response, UNAUTHORIZED


def create_response(oslc_resource):
    content_type = request.headers.get('accept')
    representation = get_content_type(content_type)
    data = oslc_resource.to_rdf(representation)

    logger.debug(f'Generating response with: Content-Type {content_type} '
                 f'RDF representation {representation} ')

    if data:
        response = make_response(data.decode('utf-8'), 200)
    else:
        response = make_response({'message': 'No content'}, 204)

    response.headers['Content-Type'] = content_type
    return response


@oslc_ns.route('')
class ServiceProvider(Resource):

    @login_required
    @api.doc(security='apikey')
    def get(self):
        oslc_resource = OSLCResource(current_app.config['SOURCE_BASE_URI'], current_user.access_token)
        oslc_resource.get_service_provider(request.base_url)

        if oslc_resource:
            response = create_response(oslc_resource)
            return response
        else:
            return make_response('Could not connect with the data source.', 404)


@oslc_ns.route('/<item_type>')
class QueryCapability(Resource):

    @login_required
    @api.doc(parser=paging_parser)
    @api.doc(security='apikey')
    def get(self, item_type: str):
        args = paging_parser.parse_args()
        paging: bool = args['oslc.paging']
        page_size: int = args['oslc.pageSize']
        page_no: int = args['oslc.pageNo']

        url_sp = url_for('api.oslc_service_provider', _external=True)
        logger.debug(f'{page_no}-{page_size}-{paging}')

        oslc_resource = OSLCResource(current_app.config['SOURCE_BASE_URI'], current_user.access_token)
        oslc_resource.get_query_capabilities(
            item_type=item_type,
            url=request.base_url,
            url_sp=url_sp,
            paging=paging,
            page_size=page_size,
            page_no=page_no
        )
        response = create_response(oslc_resource)

        if response.status_code != 204:
            return response
        else:
            return make_response(
                f'The Item Type {item_type} does not exist or an error occurred during the RDF translation', 400)


@oslc_ns.route('/<item_type>/<config_id>')
class QueryResource(Resource):

    @login_required
    @api.doc(parser=config_parser)
    @api.doc(security='apikey')
    def get(self, item_type: str, config_id: str):
        args = config_parser.parse_args()
        config_context_qs: str = args['oslc_config.context']
        config_context_header: str = args['Configuration-Context']

        config_context = ''

        if config_context_qs is not (None and ' ' and ''):
            config_context = config_context_qs
        elif config_context_header is not (None and ' ' and ''):
            config_context = config_context_header

        url_sp = url_for('api.oslc_service_provider', _external=True)
        oslc_resource = OSLCResource(current_app.config['SOURCE_BASE_URI'], current_user.access_token)
        resource = oslc_resource.get_query_resource(item_type, config_id,
                                                    url=request.base_url, url_sp=url_sp,
                                                    config_context=config_context)
        if resource:
            response = create_response(oslc_resource)
            return response
        else:
            return make_response(
                f'The Item {item_type} with the Config ID: {config_id} and Config Context: {config_context}'
                f' does not exist or an error occurred during the RDF translation',
                400)


@oslc_ns.route('/<item_type>/resourceShape')
class ResourceShape(Resource):

    @login_required
    @api.doc(security='apikey')
    def get(self, item_type):
        url_sp = url_for('api.oslc_service_provider', _external=True)
        oslc_resource = OSLCResource(current_app.config['SOURCE_BASE_URI'], current_user.access_token)
        oslc_resource.get_resource_shape(item_type, request.base_url, url_sp=url_sp)

        if oslc_resource:
            response = create_response(oslc_resource)
            return response
        else:
            return make_response(
                f'The Item Type {item_type} does not exist or an error occurred during the RDF translation', 400)
