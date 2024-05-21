import uuid
import os
from datetime import datetime
from django.db import models
from django.dispatch import receiver
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from easy_thumbnails.fields import ThumbnailerImageField
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from easy_thumbnails.signals import saved_file
from easy_thumbnails.signal_handlers import generate_aliases_global
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError

from src.common.helpers import build_absolute_uri
from src.notifications.services import notify, ACTIVITY_USER_RESETS_PASS

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """

        # email = self.normalize_email(email)
        # user = self.model(email=email, **extra_fields)
        # user.role = Roles.CUSTOMER)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

    def create_instructor(self, email, password, **extra_fields):
        """
        Create and save an instructor with the given email and password.
        """

        # email = self.normalize_email(email)
        # user = self.model(email=email, **extra_fields)
        # user.role = Roles.CUSTOMER)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Instructor must have is_staff=True.'))
        return self.create_user(email, password, **extra_fields)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    """
    reset_password_path = reverse('password_reset:reset-password-confirm')
    context = {
        'email': reset_password_token.user.email,
        'reset_password_url': build_absolute_uri(f'{reset_password_path}?token={reset_password_token.key}'),
    }

    notify(ACTIVITY_USER_RESETS_PASS, context=context, email_to=[reset_password_token.user.email])

def validate_image_file_extension(value):
    ext = os.path.splitext(value)[1]  # [0] returns path & filename
    valid_extensions = ['.svg', '.png', '.jpg', '.jpeg' ] # populate with the extensions that you allow / want
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')
    
class User(AbstractUser):
    class Roles(models.TextChoices):
        SUPER = "SUPER", "Super"
        ADMIN = "ADMIN", "Admin"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        STUDENT = "STUDENT", "Student"
    

    username = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.CharField(default='default.png', blank=True, null=True, max_length=256, validators=[validate_image_file_extension])
    email = models.EmailField(max_length=254, unique=True)
    level = models.IntegerField(blank=True, null=True )
    phone = models.CharField(blank=True, null=True, max_length=250)
    matric_number = models.CharField(blank=True, null=True, max_length=250)
    department = models.CharField(blank=True, null=True, max_length=250)
    office = models.CharField(blank=True, null=True, max_length=250)
    title = models.CharField(blank=True, null=True, max_length=250)
    first_name = models.CharField(blank=True, null=True, max_length=250)
    last_name = models.CharField(blank=True, null=True, max_length=250)
    role = models.CharField(max_length=50, choices=Roles.choices, default=Roles.STUDENT)
    email_confirmation = models.BooleanField(default=False)
    date_joined = models.CharField(max_length=50, default=datetime.now(), null=True, blank=False)
    progress =  ArrayField(
        models.IntegerField(blank=True),
        null=True
    )
    referral_code = models.TextField(max_length=50, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    objects = CustomUserManager()

    # def email_user(self, *args, **kwargs):
    #     sengridMail=mail.SendEmail()
    #     print(args, self.email)
    #     sengridMail.send_email(
    #         '{}'.format(args[0]),
    #         [self.email],
    #         '{}'.format(args[1]),
    #         '{}'.format(args[2]),
    #         '{}'.format(args[3])
    #     )

    def get_full_name(self) -> str:
        return super().get_full_name() 


    def get_tokens(self):
        refresh = RefreshToken.for_user(self)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

saved_file.connect(generate_aliases_global)
