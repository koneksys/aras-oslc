from flask_login import UserMixin


class User(UserMixin):
    id = None
    username = None
    id_token = None
    access_token = None
    expires_in = None
    expires_at = None

    def __init__(self, username, id_token=None, access_token=None, expires_in=None, expires_at=None):
        self.id = username
        self.username = username
        self.id_token = id_token
        self.access_token = access_token
        self.expires_in = expires_in
        self.expires_at = expires_at

    def __repr__(self):
        return f'<User: [username: {self.username}]>'
