import logging
from rest_framework import serializers
from django.contrib.auth import authenticate
from users import models
from django.contrib.auth import get_user_model
import uuid
from app_common.models import Banner, ContactMessage


class SignupSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = models.User
        fields = ['full_name', 'email', 'contact', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True},
            
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        if len(data['password']) < 6:
            raise serializers.ValidationError('Password Length is less than 6..')

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = models.User(**validated_data)
        user.set_password(validated_data['password'])
        user.is_active = True
        user.save()
        return user
   
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Must include 'email' and 'password'.")

        User = get_user_model()
        
        # Authenticate using email as username
        user = authenticate(username=email, password=password)

        if user:
            if not user.is_active:
                raise serializers.ValidationError("Account is inactive.", code='authorization')
        else:
            raise serializers.ValidationError("Invalid credentials.", code='authorization')

        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        exclude = ["password"] 

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ['full_name', 'email', 'contact']

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ['full_name', 'email', 'contact', 'profile_pic']

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not models.User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value
    
class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        exclude = ["password"]

class AddressSerializer(serializers.Serializer):
    # id = serializers.UUIDField(format='hex_verbose')
    Address1 = serializers.CharField(max_length=255)
    Address2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    country = serializers.CharField(max_length=255)
    state = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=255)
    mobile_no = serializers.CharField(max_length=20)
    pincode = serializers.CharField(max_length=10)

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'contact', 'message']

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'image', 'order', 'active']