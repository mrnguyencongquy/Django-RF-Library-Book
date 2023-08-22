from django.test import TestCase

# Create your tests here.
# Create your tests here.
from passlib.hash import django_pbkdf2_sha256 as handler


h = handler.hash("0")
print(h)