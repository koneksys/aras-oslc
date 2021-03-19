
class ArasAPIBaseError(Exception):
    """Base Exception for all errors in ARAS API."""

    #: short-string error code
    error = None
    #: long-string to describe this error
    description = ''
    #: web page that describes this error
    uri = None

    def __init__(self, error=None, description=None, uri=None):
        if error is not None:
            self.error = error
        if description is not None:
            self.description = description
        if uri is not None:
            self.uri = uri

        message = '{}: {}'.format(self.error, self.description)
        super(ArasAPIBaseError, self).__init__(message)

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.error)


class OAuthError(ArasAPIBaseError):
    error = 'oauth_error'
