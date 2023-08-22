from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'is_admin', 'register_date', 'last_login', 'created_by']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'created_by': {
                'read_only': True,
            },
            'register_date': {
                'read_only': True
            }
        }
  
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = ('new_password', 'current_password')


class UpdateUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    password = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'password', 'email')
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'read_only': True
            }
        }

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))
        instance.save()
        return instance


