from datetime import datetime, timedelta
import jwt
from django.conf import settings

class UserAuthentication:
    def generate_access_token(self, user):
        access_token_payload = {
            'user_id': str(user.id),
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow(),
        }
        access_token = jwt.encode(access_token_payload, settings.SECRET_KEY, algorithm='HS256')
        return access_token

