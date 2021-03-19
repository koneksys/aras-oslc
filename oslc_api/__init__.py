import logging
import os

from flask import Flask

from config import environments

logger = logging.getLogger(__name__)


def create_app(app_config: str = None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)

    config_obj = environments[app_config]

    if config_obj is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the app config if passed in
        app.config.from_object(config_obj)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import auth
    auth.init_app(app)

    from . import rest_api
    rest_api.init_app(app)

    return app
