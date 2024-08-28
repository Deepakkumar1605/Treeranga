from rest_framework import serializers
from django.conf import settings
from users.serializers import UserSerializer
from orders.models import Order



class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:

        model =Order
        fields = '__all__'