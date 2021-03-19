import logging

from flask import g
from flask.sessions import SecureCookieSessionInterface

logger = logging.getLogger(__name__)


class CustomSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""
    def save_session(self, *args, **kwargs):
        if g.get('login_via_header'):
            logger.debug('Disabling session cookies')
            return

        logger.debug('Session cookies enabled')
        return super(CustomSessionInterface, self).save_session(*args, **kwargs)
