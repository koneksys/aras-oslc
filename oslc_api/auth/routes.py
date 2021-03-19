import logging

from flask import make_response
from flask_login import login_required, logout_user
from flask_restx import Namespace, Resource, fields
from werkzeug.exceptions import InternalServerError

from oslc_api.auth import aras_api
from oslc_api.auth.parsers import user_parser

logger = logging.getLogger(__name__)

oauth_ns = Namespace('oauth', description='OSLC Authentication', path='/api/oauth')

model = oauth_ns.model('Model', {
    'username': fields.String,
    'password': fields.String
})


@oauth_ns.route('/login')
@oauth_ns.doc(parser=user_parser)
class Login(Resource):

    def post(self):
        args = user_parser.parse_args()
        username: str = args['username']
        password: str = args['password']

        token = aras_api.get_token(username, password)
        if token:
            return make_response(token, 200)
        else:
            return make_response('Authentication failed', 400)


@oauth_ns.route('/logout')
class Logout(Resource):

    @login_required
    def get(self):
        res = aras_api.end_session()
        if res:
            logout_user()
            return make_response({'message': 'Session ended'}, 200)

        raise InternalServerError()
