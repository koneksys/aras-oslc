class OSLCAPI:

    def __init__(self, client):
        self._client = client
        self.headers = {
            'Accept': 'text/turtle',
            'Content-Type': 'application/json'
        }

    def get_service_provider(self, header=None):
        if header:
            self.headers.update(header)

        return self._client.get(
            '/api/oslc',
            headers=self.headers
        )

    def get_query_capabilities(self, item_type):
        return self._client.get(
            '/api/oslc/' + item_type,
            headers=self.headers
        )

    def get_query_resource(self, item_type_name, item_type_id):
        return self._client.get(
            '/api/oslc/' + item_type_name + '/' + item_type_id,
            headers=self.headers
        )

    def get_components(self, item_type_name):
        return self._client.get(
            '/api/oslc/config/' + item_type_name + '/components',
            headers=self.headers
        )

    def get_component(self, item_type_name, config_id):
        return self._client.get(
            '/api/oslc/config/' + item_type_name + '/component/' + config_id,
            headers=self.headers
        )

    def get_configurations(self, item_type_name, config_id):
        return self._client.get(
            '/api/oslc/config/' + item_type_name + '/component/' + config_id + '/configurations',
            headers=self.headers
        )
