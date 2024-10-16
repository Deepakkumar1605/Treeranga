from django.db import models
from django.contrib.auth.models import AbstractBaseUser ,PermissionsMixin
from PIL import Image
from django.urls import reverse
from users.manager import MyAccountManager
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from helpers import utils
import uuid
from django.conf import settings
from helpers.methods import request_deletion, cancel_deletion


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True, unique=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    contact = models.CharField(max_length=10, null=True, blank=True, unique=True)
    profile_pic = models.ImageField(upload_to="user_profile_pic/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    address = models.JSONField(default=dict, null=True, blank=True)
    deletion_requested = models.BooleanField(default=False)
    deletion_date = models.DateTimeField(null=True, blank=True)
    wallet = models.FloatField(default=0.0)
    token = models.CharField(max_length=100, null=True, blank=True)
    meta_data = models.JSONField(default=dict)

    USERNAME_FIELD = "email"	
    REQUIRED_FIELDS = ["password"]

    objects = MyAccountManager()

    def request_deletion(self):
        request_deletion(self)

    def cancel_deletion(self):
        cancel_deletion(self)

    def __str__(self):
        return self.email

    

    def generate_reset_password_token(self):
        token = str(uuid.uuid4())
        self.token = token
        self.save()
        return token

    def reset_password(self, token, new_password):
        if self.token == token:
            self.set_password(new_password)
            self.token = None  # Clear the token after password reset
            self.save()
            return True
        return False