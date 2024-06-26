import factory


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'users.User'
        django_get_or_create = ('email',)

    id = factory.Faker('uuid4')
    password = factory.PostGenerationMethodCall('set_password', 'asdf')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
