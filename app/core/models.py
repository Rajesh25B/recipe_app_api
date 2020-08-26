from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                        PermissionsMixin
# Create your models here.
# AbstractBaseUser provides the core implementation of a user model,
# including hashed passwords and tokenized password resets.


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """ creates a new user and saves """
        if not email:
            raise ValueError('Enter a valid Email Address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """creating a superuser"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Create a custom user model that supports using email instead username"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'