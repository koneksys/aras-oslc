import json
import logging

from flask import Blueprint, request
from flask_restx import Api
from werkzeug.exceptions import HTTPException

from oslc_api.rest_api.representations import output_rdf

logger = logging.getLogger(__name__)

blueprint = Blueprint('api', __name__)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-ARAS-ACCESS-TOKEN',
        'description': 'Access Token for ARAS OSLC API'
    }
}

api = Api(
    app=blueprint,
    title='ARAS OSLC API',
    version='0.1.0',
    description='An OSLC API to expose ItemTypes',
    authorizations=authorizations
)

api.representations['application/rdf+xml'] = output_rdf
api.representations['application/json-ld'] = output_rdf
api.representations['text/turtle'] = output_rdf


@blueprint.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


@blueprint.before_request
def clean_request():
    req_args = request.args
    new_args = dict()
    for arg in req_args:
        new_arg = arg.replace('&', '').replace('amp', '').replace(';', '')
        new_args[new_arg] = req_args[arg]

    request.args = new_args


def init_app(app):
    """
    Initializing the REST API using Flask-RESTx extension
    :param app: Flask application
    :return: None
    """

    from oslc_api.rest_api.routes import oslc_ns
    api.add_namespace(oslc_ns)

    from oslc_api.auth.routes import oauth_ns
    api.add_namespace(oauth_ns)

    from oslc_api.rest_api.config import config_ns
    api.add_namespace(config_ns)

    app.register_blueprint(blueprint)
