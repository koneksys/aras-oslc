from os import environ

from oslc_api import create_app


try:
    environ.get('FLASK_ENV')
except KeyError as e:
    print("Please, provide the environment variable FLASK_ENV. It is required.")
    exit()

app_config = environ.get('FLASK_ENV')

app = create_app(app_config=app_config)

if __name__ == '__main__':
    app.run()
