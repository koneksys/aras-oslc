import os
from os import environ

from dotenv import load_dotenv

base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir, '.env'))


class BaseConfig:
    DEBUG = False
    TESTING = False

    BINARY_SECRET_KEY = b'R\x0f\xa8\x9d\xcag\xb2\xe4\x9b\x01\x90(Y\x10\xe3?W0\xc6\xb0\xf4\t\xe11\xcd\x8c,@\x0fm\x8a\xf4'

    SECRET_KEY = environ.get('SECRET_KEY') or BINARY_SECRET_KEY
    DATABASE_URL = environ.get('DATABASE_URL', None)
    DATABASE_PREFIX = environ.get('DATABASE_PREFIX', None)

    OAUTH_CLIENT_NAME = environ.get('OAUTH_CLIENT_NAME') or 'oauth_client'
    OAUTH_CLIENT_ID = environ.get('OAUTH_CLIENT_ID') or 'IOMApp'
    OAUTH_CLIENT_SECRET = environ.get('OAUTH_CLIENT_SECRET') or None

    SWAGGER_UI_OAUTH_CLIENT_ID = OAUTH_CLIENT_ID

    SOURCE_BASE_API_URI = environ.get('SOURCE_BASE_API_URI')
    SOURCE_BASE_URI = SOURCE_BASE_API_URI + '/server/odata/'

    SOURCE_DATABASE = environ.get('SOURCE_DATABASE')


class ProductionConfig(BaseConfig):
    FLASK_ENV = 'production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True


environments = {
    'production': ProductionConfig,
    'development': DevelopmentConfig,
    'testing': TestingConfig
}
