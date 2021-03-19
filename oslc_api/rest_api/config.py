from flask import request, current_app, make_response
from flask_login import login_required, current_user
from flask_restx import Namespace, Resource

from oslc_api.aras.resources import OSLCResource
from oslc_api.rest_api import api, authorizations
from oslc_api.rest_api.parsers import paging_parser
from oslc_api.rest_api.routes import create_response

config_ns = Namespace('config', description='OSLC Configuration',
                      path='/api/oslc/config', authorizations=authorizations)


@config_ns.route('/<item_type>/components')
class Components(Resource):

    @login_required
    @api.doc(parser=paging_parser)
    @api.doc(security='apikey')
    def get(self, item_type: str):
        args = paging_parser.parse_args()
        paging: bool = args['oslc.paging']
        page_size: int = args['oslc.pageSize']
        page_no: int = args['oslc.pageNo']

        oslc_resource = OSLCResource(current_app.config['SOURCE_BASE_URI'], current_user.access_token)
        oslc_resource.get_components(
            item_type=item_type,
            url=request.base_url,
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


@config_ns.route('/<item_type>/component/<config_id>')
class Component(Resource):

    @login_required
    @api.doc(security='apikey')
    def get(self, item_type: str, config_id: str):
        oslc_resource = OSLCResource(current_app.config['SOURCE_BASE_URI'], current_user.access_token)
        oslc_resource.get_component(item_type, config_id, request.base_url)

        response = create_response(oslc_resource)
        if response.status_code != 204:
            return response
        else:
            return make_response(
                f'The Item {item_type} with the ID: {config_id} does not exist or an error occurred during the RDF translation',
                400)


@config_ns.route('/<item_type>/component/<config_id>/configurations')
class Configurations(Resource):

    @login_required
    @api.doc(security='apikey')
    def get(self, item_type: str, config_id: str):
        oslc_resource = OSLCResource(current_app.config['SOURCE_BASE_URI'], current_user.access_token)
        oslc_resource.get_configurations(item_type, config_id, request.base_url)

        response = create_response(oslc_resource)
        if response.status_code != 204:
            return response
        else:
            return make_response(
                f'The Item {item_type} with the ID: {config_id} does not exist or an error occurred during the RDF translation',
                400)


@config_ns.route('/<item_type>/component/<config_id>/stream/<stream_id>')
class Stream(Resource):

    @login_required
    @api.doc(security='apikey')
    def get(self, item_type: str, config_id: str, stream_id: str):
        oslc_resource = OSLCResource(current_app.config['SOURCE_BASE_URI'], current_user.access_token)
        oslc_resource.get_stream(item_type, config_id, stream_id, request.base_url)

        response = create_response(oslc_resource)
        if response.status_code != 204:
            return response
        else:
            return make_response(
                f'The Item {item_type} with the Config ID: {config_id} and the Stream ID: {stream_id} '
                f'does not exist or an error occurred during the RDF translation',
                400)
