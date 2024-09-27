from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
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

from payment.payment_views.user_payment_views import convert_decimals_to_str
from payment.razorpay import verify_signature
from payment.serializer import PaymentSuccessSerializer
from product.models import SimpleProduct
from product_variations.models import VariantProduct
from users.user_views.emails import send_template_email

# class PaymentSuccessAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     @swagger_auto_schema(
#             tags=["Payment"],
#             operation_description="payment",
#             responses={
#                 200: 'Successfully payment done',
#                 401: 'Unauthorized',
#                 404: 'Category not found'
#             }
#         )
#     def post(self, request):
#         user = request.user
#         serializer = PaymentSuccessSerializer(data=request.data)
        
#         if serializer.is_valid():
#             data = serializer.validated_data
#             address_id = data.get('address_id')
#             payment_method = data.get('payment_method')
#             print(address_id,payment_method)
#             try:
#                 cart = Cart.objects.get(user=user)
#             except Cart.DoesNotExist:
#                 return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

#             # Fetch order details
#             cart_serializer = CartSerializer(cart)
#             order_details = cart_serializer.data
#             ord_meta_data = {k: v for d in order_details.values() for k, v in d.items()}
#             t_price = float(ord_meta_data.get('final_cart_value', 0))


#             user_addresses = user.address
        
#             selected_address = next((addr for addr in user_addresses if addr['id'] == str(address_id)), None)
#             print(selected_address,"selected_address")
#             if not selected_address:
#                 return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

#             try:
#                 if payment_method == 'razorpay':
#                     razorpay_payment_id = data.get('razorpay_payment_id')
#                     razorpay_order_id = data.get('razorpay_order_id')
#                     razorpay_signature = data.get('razorpay_signature')

#                     if not verify_signature(data):
#                         return Response({"error": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)

#                     # Create and save the order
#                     order = Order(
#                         user=user,
#                         full_name=cart.user.full_name,
#                         email=cart.user.email,
#                         products=cart.products,
#                         order_value=t_price,
#                         address=selected_address,
#                         order_meta_data=ord_meta_data,
#                         razorpay_payment_id=razorpay_payment_id,
#                         razorpay_order_id=razorpay_order_id,
#                         razorpay_signature=razorpay_signature,
#                     )
#                     order.save()

#                     # Send confirmation email
#                     context = {
#                         'full_name': user.full_name,
#                         'email': user.email,
#                         'order_value': t_price,
#                         'order_details': ord_meta_data,
#                         'address': selected_address,
#                     }
#                     send_template_email(
#                         subject='Order Confirmation',
#                         template_name='users/email/order_confirmation.html',
#                         context=context,
#                         recipient_list=[user.email]
#                     )

#                     cart.delete()
#                     return Response({"message": "Order Successful!"}, status=status.HTTP_200_OK)

#                 elif payment_method == 'cod':
#                     # Create and save the order for COD
#                     print("hiii")
#                     order = Order(
#                         user=user,
#                         full_name=cart.user.full_name,
#                         email=cart.user.email,
#                         products=cart.products,
#                         order_value=t_price,
#                         address=selected_address,
#                         order_meta_data=ord_meta_data,
#                         payment_method='cod',
#                         payment_status='Pending'  # Set payment status to Pending for COD
#                     )
#                     order.save()

#                     # Send confirmation email
#                     context = {
#                         'full_name': user.full_name,
#                         'email': user.email,
#                         'order_value': t_price,
#                         'order_details': ord_meta_data,
#                         'address': selected_address,
#                     }
#                     send_template_email(
#                         subject='Order Confirmation',
#                         template_name='users/email/order_confirmation.html',
#                         context=context,
#                         recipient_list=[user.email]
#                     )

#                     cart.delete()
#                     return Response({"message": "Order placed successfully. Cash on Delivery selected.","order_uid":order.uid}, status=status.HTTP_200_OK)

#                 else:
#                     return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

#             except Exception as e:
#                 return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
        
        # Fetch the cart
        cart = get_object_or_404(Cart, user=user)

        data = request.data
        address_id = data.get('address_id')
        payment_method = data.get('payment_method')

        # Fetch order details
        order_details = CartSerializer(cart).data
        ord_meta_data = {k: v for d in order_details.values() for k, v in d.items()}
        ord_meta_data = convert_decimals_to_str(ord_meta_data)

        t_price = float(ord_meta_data.get('final_cart_value', 0))
        
        # Validate address
        user_addresses = user.address
        selected_address = next((addr for addr in user_addresses if addr['id'] == address_id), None)
        if not selected_address:
            return Response({"error": "Address not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if payment_method == 'razorpay':
                razorpay_payment_id = data.get('razorpay_payment_id')
                razorpay_order_id = data.get('razorpay_order_id')
                razorpay_signature = data.get('razorpay_signature')

                if not verify_signature(data):
                    return Response({"error": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)

                order = self.create_order(user, cart, selected_address, ord_meta_data, 
                                           razorpay_payment_id, razorpay_order_id, razorpay_signature, t_price)

            elif payment_method == 'cod':
                order = self.create_order(user, cart, selected_address, ord_meta_data, 
                                           payment_method='cod', payment_status='Pending', order_value=t_price)

            else:
                return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

            # Reduce stock for each product in the cart
            self.update_product_stock(cart)

            # Send confirmation email
            self.send_confirmation_email(user, t_price, ord_meta_data, selected_address)

            # Clear the cart
            cart.delete()
            return Response({"message": "Order Successful!"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred while processing your order: {str(e)}"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create_order(self, user, cart, selected_address, ord_meta_data, 
                     razorpay_payment_id=None, razorpay_order_id=None, 
                     razorpay_signature=None, payment_method='cod', 
                     payment_status='Pending', order_value=0):
        order = Order(
            user=user,
            full_name=cart.user.full_name,
            email=cart.user.email,
            products=cart.products,
            order_value=float(order_value),
            address=selected_address,
            order_meta_data=ord_meta_data,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_signature=razorpay_signature,
            payment_method=payment_method,
            payment_status=payment_status
        )
        order.save()
        return order

    def update_product_stock(self, cart):
        for product_key, product_data in cart.products.items():
            product_id = product_data['info']['product_id']
            quantity = product_data['quantity']
            product_type = product_data['info']['variant']

            if product_type == "yes":
                variant_product = get_object_or_404(VariantProduct, id=product_id)
                if variant_product.stock >= quantity:
                    variant_product.stock -= quantity
                    variant_product.save()
                else:
                    raise ValueError(f"Insufficient stock for variant product {variant_product.product.name}.")

            elif product_type == "no":
                simple_product = get_object_or_404(SimpleProduct, id=product_id)
                if simple_product.stock >= quantity:
                    simple_product.stock -= quantity
                    simple_product.save()
                else:
                    raise ValueError(f"Insufficient stock for simple product {simple_product.product.name}.")

    def send_confirmation_email(self, user, order_value, order_details, address):
        context = {
            'full_name': user.full_name,
            'email': user.email,
            'order_value': order_value,
            'order_details': order_details,
            'address': address,
        }
        send_template_email(
            subject='Order Confirmation',
            template_name='users/email/order_confirmation.html',
            context=context,
            recipient_list=[user.email]
        )

def convert_decimals_to_str(data):
    if isinstance(data, dict):
        return {k: convert_decimals_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimals_to_str(v) for v in data]
    elif isinstance(data, Decimal):
        return str(data)
    return data