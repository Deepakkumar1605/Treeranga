from django.shortcuts import redirect
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from cart.models import Cart
from orders.models import Order
from drf_yasg import openapi
from cart.serializer import CartSerializer
import json

from payment.razorpay import verify_signature
from payment.serializer import PaymentSuccessSerializer
from users.user_views.emails import send_template_email

class PaymentSuccessAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
            tags=["Payment"],
            operation_description="payment",
            responses={
                200: 'Successfully payment done',
                401: 'Unauthorized',
                404: 'Category not found'
            }
        )
    def post(self, request):
        user = request.user
        serializer = PaymentSuccessSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            address_id = data.get('address_id')
            payment_method = data.get('payment_method')
            print(address_id,payment_method)
            try:
                cart = Cart.objects.get(user=user)
            except Cart.DoesNotExist:
                return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

            # Fetch order details
            cart_serializer = CartSerializer(cart)
            order_details = cart_serializer.data
            ord_meta_data = {k: v for d in order_details.values() for k, v in d.items()}
            t_price = float(ord_meta_data.get('final_cart_value', 0))


            user_addresses = user.address
        
            selected_address = next((addr for addr in user_addresses if addr['id'] == str(address_id)), None)
            print(selected_address,"selected_address")
            if not selected_address:
                return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

            try:
                if payment_method == 'razorpay':
                    razorpay_payment_id = data.get('razorpay_payment_id')
                    razorpay_order_id = data.get('razorpay_order_id')
                    razorpay_signature = data.get('razorpay_signature')

                    if not verify_signature(data):
                        return Response({"error": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)

                    # Create and save the order
                    order = Order(
                        user=user,
                        full_name=cart.user.full_name,
                        email=cart.user.email,
                        products=cart.products,
                        order_value=t_price,
                        address=selected_address,
                        order_meta_data=ord_meta_data,
                        razorpay_payment_id=razorpay_payment_id,
                        razorpay_order_id=razorpay_order_id,
                        razorpay_signature=razorpay_signature,
                    )
                    order.save()

                    # Send confirmation email
                    context = {
                        'full_name': user.full_name,
                        'email': user.email,
                        'order_value': t_price,
                        'order_details': ord_meta_data,
                        'address': selected_address,
                    }
                    send_template_email(
                        subject='Order Confirmation',
                        template_name='users/email/order_confirmation.html',
                        context=context,
                        recipient_list=[user.email]
                    )

                    cart.delete()
                    return Response({"message": "Order Successful!"}, status=status.HTTP_200_OK)

                elif payment_method == 'cod':
                    # Create and save the order for COD
                    print("hiii")
                    order = Order(
                        user=user,
                        full_name=cart.user.full_name,
                        email=cart.user.email,
                        products=cart.products,
                        order_value=t_price,
                        address=selected_address,
                        order_meta_data=ord_meta_data,
                        payment_method='cod',
                        payment_status='Pending'  # Set payment status to Pending for COD
                    )
                    order.save()

                    # Send confirmation email
                    context = {
                        'full_name': user.full_name,
                        'email': user.email,
                        'order_value': t_price,
                        'order_details': ord_meta_data,
                        'address': selected_address,
                    }
                    send_template_email(
                        subject='Order Confirmation',
                        template_name='users/email/order_confirmation.html',
                        context=context,
                        recipient_list=[user.email]
                    )

                    cart.delete()
                    return Response({"message": "Order placed successfully. Cash on Delivery selected.","order_uid":order.uid}, status=status.HTTP_200_OK)

                else:
                    return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)