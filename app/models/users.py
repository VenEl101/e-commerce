
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from app.manager import CustomUserManager


class User(AbstractUser):

    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'admin'
        USER = 'USER', 'user'
        SELLER = 'SELLER', 'seller'

    first_name = models.CharField(_('first name'), max_length=100, blank=False, null=False)
    last_name = models.CharField(_('last name'), max_length=100, blank=False, null=False)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=25, choices=Roles, default=Roles.USER)


    objects = CustomUserManager()

    def __str__(self):
        return self.email


