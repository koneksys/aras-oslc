import os

from oslc_api.aras.data import load_from_json_file


def test_load_from_json_invalid_file():
    """
    GIVEN an invalid name of json file
    WHEN loading the values from the file
    THEN the result will be an empty dict and @odata.context equal to None
    """

    file = os.path.join('data', 'invalid.json')
    data = load_from_json_file(file)

    assert data is not None
    assert '@odata.context' not in data, 'The context value of the dictionary is not empty'
    assert 'value' not in data, 'The value attribute of the dictionary is not empty'


def test_load_from_json_file():
    """
    GIVEN a valid name of json file with the list of item types
    WHEN loading the values from the file
    THEN check if the response contain the @odata.context and value attributes
    """

    file = os.path.join('data', 'sourceItemTypes.json')
    data = load_from_json_file(file)

    assert data is not None
    assert '@odata.context' in data
    assert 'value' in data
