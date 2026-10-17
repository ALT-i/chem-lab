# Every test below is commented out; the module only existed to carry these
# imports. `nose` is unmaintained and does not support modern Python, so it
# is not in dev.txt -- importing it here broke collection of the whole suite.
# If these tests are revived, use plain assertSomething from TestCase.
from django.test import TestCase
from django.contrib.auth.hashers import check_password
from ..serializers import CreateUserSerializer


# class TestCreateUserSerializer(TestCase):
#     def setUp(self):
#         self.user_data = {'username': 'test', 'password': 'test'}

#     def test_serializer_with_empty_data(self):
#         serializer = CreateUserSerializer(data={})
#         eq_(serializer.is_valid(), False)

#     def test_serializer_with_valid_data(self):
#         serializer = CreateUserSerializer(data=self.user_data)
#         ok_(serializer.is_valid())

#     def test_serializer_hashes_password(self):
#         serializer = CreateUserSerializer(data=self.user_data)
#         ok_(serializer.is_valid())

#         user = serializer.save()
#         ok_(check_password(self.user_data.get('password'), user.password))
