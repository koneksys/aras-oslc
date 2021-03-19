import json
import os


def load_from_json_file(file_name: str) -> dict:
    data = dict()
    if os.path.isfile(file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)

    return data
