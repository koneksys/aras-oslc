from flask_restx import inputs, reqparse


paging_parser = reqparse.RequestParser()
paging_parser.add_argument(
    name="oslc.paging",
    type=inputs.boolean,
    required=False,
    default=False,
    help="The response required as paging",
    location="args"
)
paging_parser.add_argument(
    name="oslc.pageSize",
    type=int,
    required=False,
    default=0,
    help="The number of elements on each page",
    location="args"
)
paging_parser.add_argument(
    name="oslc.pageNo",
    type=int,
    required=False,
    default=0,
    help="The number of the page to get",
    location="args"
)


config_parser = reqparse.RequestParser()
config_parser.add_argument(
    name="Configuration-Context",
    # type=str,
    # required=False,
    # default='',
    # help="The stream ID for the Item Type ",
    location="headers"
)
config_parser.add_argument(
    name="oslc_config.context",
    # type=str,
    # required=False,
    # default='',
    # help="The stream ID for the Item Type ",
    location="args"
)
# config_parser.add_argument(
#     name="item_id",
#     type=str,
#     required=False,
#     default='',
#     help="The Item ID for the Item Type",
#     location="args"
# )
