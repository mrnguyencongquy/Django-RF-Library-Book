from helpers import helper


class CreateUserHelper:
    def change_response(self, serializer):
        return {
            'id': serializer.data.get('id'),
            'email': serializer.data.get('email'),
            'firstName': serializer.data.get('first_name', ''),
            'lastName': serializer.data.get('last_name', '')
        }

    def change_request(self, request):
        return {
            'username': request.data.get('userName'),
            'email': request.data.get('email'),
            'password': request.data.get('password'),
            'first_name': request.data.get('firstName'),
            'last_name': request.data.get('lastName')
        }

    def add_create_by_to_request(self, user=None):
        return user.email if user else ''

class UpdateUserHelper:
    def change_request(self, request):
        result = {}
        if request.data.get('password'):
            result['password'] = request.data.get('password')
        if request.data.get('firstName'):
            result['first_name'] = request.data.get('firstName')
        if request.data.get('lastName'):
            result['last_name'] = request.data.get('lastName')
        return result

class GetProfileHelper:
    def change_response(self, serializer):
        return {
            'id': serializer.data.get('id'),
            'email': serializer.data.get('email'),
            'firstName': serializer.data.get('first_name', ''),
            'lastName': serializer.data.get('last_name', ''),
            'isAdmin': serializer.data.get('is_admin')
        }

class ChangePasswordHelper:
    def change_request(self, request):
        return {
            'new_password': request.data.get('newPassword'),
            'current_password': request.data.get('currentPassword')
        }

class ListUserHelper(helper.MappingHelper):
    MAPPING_USER = {
        "id": "id",
        "email": "email",
        "firstName": "first_name",
        "lastName": "last_name",
        "registerDate": 'register_date',
        "createdBy": "created_by"
    }

    def change_response_user(self, dataset):
        return super().change_response(dataset, self.MAPPING_USER)



