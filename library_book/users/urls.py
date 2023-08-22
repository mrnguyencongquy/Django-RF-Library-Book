from django.urls import path
from .views import CreateUserView, LoginView, GetProfileView, LogoutView, ChangePasswordView, DeleteUserView, \
    UpdateUserView, ListUsers

urlpatterns = [
    path('createUser', CreateUserView.as_view()),
    path('login', LoginView.as_view()),
    path('getProfile', GetProfileView.as_view()),
    path('logout', LogoutView.as_view()),
    path('changePassword', ChangePasswordView.as_view()),
    path('deleteUser/<uuid:pk>', DeleteUserView.as_view()),
    path('updateUser/<uuid:pk>', UpdateUserView.as_view()),
    path('listUsers', ListUsers.as_view())
]