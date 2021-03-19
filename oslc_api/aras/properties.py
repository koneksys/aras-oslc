
# Create a Class for RDF Properties
class RDFProperty:
    def __init__(self, name, datatype, datasource, required):
        self.name = name
        self.dataType = datatype
        self.dataSource = datasource
        self.required = required
