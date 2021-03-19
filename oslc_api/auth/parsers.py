from flask_restx import reqparse

user_parser = reqparse.RequestParser()

user_parser.add_argument(
    name="username",
    type=str,
    required=True,
    help="The username or id of the user who wants to authenticate on Aras",
    # location='args'
    location='form'
)

user_parser.add_argument(
    name="password",
    type=str,
    # format="password",
    required=True,
    help="The password or secret of the user who wants to authenticate on Aras",
    # location='args'
    location='form'
)
