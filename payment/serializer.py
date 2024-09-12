from rest_framework import serializers
from uuid import UUID

class PaymentSuccessSerializer(serializers.Serializer):
    address_id = serializers.UUIDField()
    payment_method = serializers.ChoiceField(choices=['razorpay', 'cod'])
    razorpay_payment_id = serializers.CharField(required=False)
    razorpay_order_id = serializers.CharField(required=False)
    razorpay_signature = serializers.CharField(required=False)

    def validate_address_id(self, value):
        try:
            # Validate if the UUID is valid
            UUID(str(value))
        except ValueError:
            raise serializers.ValidationError("Invalid UUID format.")
        return value
