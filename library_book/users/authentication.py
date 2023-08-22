from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.authentication import BaseAuthentication
import jwt
from .models import User
from django.conf import settings

from helpers import helper

import logging
logger = logging.getLogger(__name__)

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None
        try:
            access_token = authorization_header.split(' ')[1]
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.filter(id=payload['user_id']).first()
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        return (user, None)

class AdminUserPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            user = CustomJWTAuthentication.authenticate(CustomJWTAuthentication, request)[0]
            is_admin = user.is_admin
            if not is_admin:
                raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                            status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        return is_admin