from rest_framework import status
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import User
from collections import OrderedDict
from .utils import UserAuthentication
from .authentication import AdminUserPermission
from .serializers import UserSerializer, ChangePasswordSerializer, UpdateUserSerializer

from helpers import helper
from helpers import users_helper

import logging
logger = logging.getLogger(__name__)

create_user_helper = users_helper.CreateUserHelper()
get_profile_helper = users_helper.GetProfileHelper()
update_user_helper = users_helper.UpdateUserHelper()
change_password_helper = users_helper.ChangePasswordHelper()
list_user_helper = users_helper.ListUserHelper()
user_authentication = UserAuthentication()

class CreateUserView(APIView):
    permission_classes = [AdminUserPermission]
    def post(self, request):
        user = request.user
        request_data = create_user_helper.change_request(request)
        serializer = UserSerializer(data=request_data)
        if not serializer.is_valid():
            if User.objects.filter(email=serializer.data.get('email')).exists():
                raise helper.WWAPIException(helper.MessageReturn.EMAIL_EXISTED_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        serializer.save(created_by=create_user_helper.add_create_by_to_request(user))
        response = create_user_helper.change_response(serializer)
        return Response(response, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.filter(email=email).first()
            if user is None or not user.check_password(password):
                raise helper.WWAPIException(helper.MessageReturn.LOGIN_MESSAGE,
                                            status_code=status.HTTP_400_BAD_REQUEST)
            response = Response(status=status.HTTP_200_OK)
            access_token = user_authentication.generate_access_token(user)
            response.data = {
                'token': access_token,
            }
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.LOGIN_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        return response


class GetProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(instance=user)
            response_data = get_profile_helper.change_response(serializer)
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(status=status.HTTP_200_OK)


class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    def update(self, request):
        user = request.user
        request_data = change_password_helper.change_request(request)
        serializer = ChangePasswordSerializer(data=request_data)
        if not serializer.is_valid():
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(serializer.data.get('current_password')):
            raise helper.WWAPIException(helper.MessageReturn.CURRENT_PASSWORD_FAILED,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        try:
            user.set_password(serializer.data.get('new_password'))
            user.save()
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)


class DeleteUserView(generics.DestroyAPIView):
    permission_classes = [AdminUserPermission]
    def delete(self, request, *args, **kwargs):
        user = User.objects.filter(id=self.kwargs.get('pk')).first()
        if not user:
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        user.delete()
        return Response(status=status.HTTP_200_OK)


class UpdateUserView(generics.UpdateAPIView):
    permission_classes = [AdminUserPermission]
    def update(self, request, *args, **kwargs):
        user = User.objects.filter(id=self.kwargs.get('pk')).first()
        if user is None:
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        request_data = update_user_helper.change_request(request)
        serializer = UpdateUserSerializer(instance=user, data=request_data)
        if not serializer.is_valid():
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_update(serializer)
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        return Response(create_user_helper.change_response(serializer), status=status.HTTP_200_OK)


class SetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'

    def get_paginated_response(self, data):
        data_convert = list_user_helper.change_response_user(data)

        response = Response(OrderedDict([
            ('userList', data_convert),
            ('totalPage', self.page.paginator.num_pages),
            ('totalUser', self.page.paginator.count),
            ('totalUserInPage', len(data_convert))
        ]))
        if response.status_code != 200:
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        return response


class ListUsers(generics.ListAPIView):
    permission_classes = [AdminUserPermission]
    queryset = User.objects.all().order_by('-register_date')
    serializer_class = UserSerializer
    pagination_class = SetPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ['email']





