from flask_login import login_user

from oslc_api.auth import User
from oslc_api.database import db


def update_user_on_session(username: str, token: dict):

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)

    user.id_token = token['id_token']
    user.access_token = token['access_token']
    user.expires_in = token['expires_in']
    user.expires_at = token['expires_at']

    db.session.add(user)
    db.session.commit()

    login_user(user)
