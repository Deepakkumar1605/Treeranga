from django.views import View
from django.shortcuts import redirect, get_object_or_404,render
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings
from app_common.error import render_error_page
from cart.models import Cart
from orders.models import Order
from product.models import SimpleProduct
from product_variations.models import VariantProduct
from users.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from cart.serializer import CartSerializer
from payment.razorpay import verify_signature  # Assuming you have a utility function for Razorpay verification
import json

from users.user_views.emails import send_template_email

app = 'payment/'

@method_decorator(csrf_exempt, name='dispatch')
class PaymentSuccess(View):
    model = Order

    def post(self, request):
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            error_message = "Cart not found."
            return render_error_page(request, error_message, status_code=400)

        try:
            data = json.loads(request.body)
            address_id = data.get('address_id')
            payment_method = data.get('payment_method')

            # Fetch order details
            order_details = CartSerializer(cart).data
            ord_meta_data = {k: v for d in order_details.values() for k, v in d.items()}
            t_price = float(ord_meta_data.get('final_cart_value', 0))

            user_addresses = user.address
            selected_address = next((addr for addr in user_addresses if addr['id'] == address_id), None)
            if not selected_address:
                error_message = "Address not found."
                return render_error_page(request, error_message, status_code=400)

            if payment_method == 'razorpay':
                razorpay_payment_id = data.get('razorpay_payment_id')
                razorpay_order_id = data.get('razorpay_order_id')
                razorpay_signature = data.get('razorpay_signature')

                if not verify_signature(data):
                    error_message = "Payment verification failed."
                    return render_error_page(request, error_message, status_code=400)

                # Create and save the order
                order = self.model(
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

                messages.success(request, "Order Successful!")
                cart.delete()
                return redirect("app_common:home")

            elif payment_method == 'cod':
                # Create and save the order for COD
                order = self.model(
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

                messages.success(request, "Order placed successfully. Cash on Delivery selected.")
                cart.delete()
                return redirect("app_common:home")

            else:
                error_message = "Invalid payment method."
                return render_error_page(request, error_message, status_code=400)

        except Exception as e:
            error_message = f"An unexpected error occurred while processing your order: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class SuccessPage(View):
    template = app + "payment_success.html"

    def get(self, request):
        try:
            return render(request, self.template)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

# @method_decorator(csrf_exempt, name='dispatch')
# class PaymentSuccess(View):
#     model = Order

#     def post(self, request):
#         user = request.user
#         try:
#             cart = Cart.objects.get(user=user)
#         except Cart.DoesNotExist:
#             error_message = "Cart not found."
#             return render_error_page(request, error_message, status_code=400)

#         try:
#             data = json.loads(request.body)
#             address_id = data.get('address_id')
#             payment_method = data.get('payment_method')

#             # Fetch order details
#             order_details = CartSerializer(cart).data
#             ord_meta_data = {k: v for d in order_details.values() for k, v in d.items()}
#             t_price = float(ord_meta_data.get('final_cart_value', 0))

#             user_addresses = user.address
#             selected_address = next((addr for addr in user_addresses if addr['id'] == address_id), None)
#             if not selected_address:
#                 error_message = "Address not found."
#                 return render_error_page(request, error_message, status_code=400)

#             if payment_method == 'razorpay':
#                 razorpay_payment_id = data.get('razorpay_payment_id')
#                 razorpay_order_id = data.get('razorpay_order_id')
#                 razorpay_signature = data.get('razorpay_signature')

#                 if not verify_signature(data):
#                     error_message = "Payment verification failed."
#                     return render_error_page(request, error_message, status_code=400)

#                 # Create and save the order
#                 order = self.model(
#                     user=user,
#                     full_name=cart.user.full_name,
#                     email=cart.user.email,
#                     products=cart.products,
#                     order_value=t_price,
#                     address=selected_address,
#                     order_meta_data=ord_meta_data,
#                     razorpay_payment_id=razorpay_payment_id,
#                     razorpay_order_id=razorpay_order_id,
#                     razorpay_signature=razorpay_signature,
#                 )

#                 order.save()

#                 # Reduce stock for each product in the cart
#                 for product_key, product_data in cart.products.items():
#                     product_id = product_data['info']['product_id']  # This ID can be for either simple or variant product
#                     quantity = product_data['quantity']
#                     product_type = product_data['info']['product_type']  # Fetch product type directly from the data

#                     try:
#                         # If it's a variant product
#                         if product_type == "variant":
#                             variant_product = VariantProduct.objects.get(id=product_id)
#                             if variant_product.stock >= quantity:
#                                 variant_product.stock -= quantity
#                                 variant_product.save()  # Update stock
#                             else:
#                                 error_message = f"Insufficient stock for variant product {variant_product.product.name}."
#                                 return render_error_page(request, error_message, status_code=400)

#                         # If it's a simple product
#                         elif product_type == "simple":
#                             simple_product = SimpleProduct.objects.get(id=product_id)
#                             if simple_product.stock >= quantity:
#                                 simple_product.stock -= quantity
#                                 simple_product.save()  # Update stock
#                             else:
#                                 error_message = f"Insufficient stock for simple product {simple_product.name}."
#                                 return render_error_page(request, error_message, status_code=400)

#                     except (VariantProduct.DoesNotExist, SimpleProduct.DoesNotExist):
#                         error_message = f"Product not found with id {product_id}."
#                         return render_error_page(request, error_message, status_code=400)

#                     except (VariantProduct.DoesNotExist, SimpleProduct.DoesNotExist):
#                         error_message = f"Product not found with id {product_id}."
#                         return render_error_page(request, error_message, status_code=400)


#                 # Send confirmation email
#                 context = {
#                     'full_name': user.full_name,
#                     'email': user.email,
#                     'order_value': t_price,
#                     'order_details': ord_meta_data,
#                     'address': selected_address,
#                 }
#                 send_template_email(
#                     subject='Order Confirmation',
#                     template_name='users/email/order_confirmation.html',
#                     context=context,
#                     recipient_list=[user.email]
#                 )

#                 messages.success(request, "Order Successful!")
#                 cart.delete()
#                 return redirect("app_common:home")

#             elif payment_method == 'cod':
#                 # Create and save the order for COD
#                 order = self.model(
#                     user=user,
#                     full_name=cart.user.full_name,
#                     email=cart.user.email,
#                     products=cart.products,
#                     order_value=t_price,
#                     address=selected_address,
#                     order_meta_data=ord_meta_data,
#                     payment_method='cod',
#                     payment_status='Pending'  # Set payment status to Pending for COD
#                 )
#                 order.save()

#             # Reduce stock for each product in the cart
#             for product_key, product_data in cart.products.items():
#                 product_id = product_data['info']['product_id']  # This ID can be for either simple or variant product
#                 quantity = product_data['quantity']
#                 product_type = product_data['info']['product_type']  # Fetch product type directly from the data

#                 try:
#                     # If it's a variant product
#                     if product_type == "variant":
#                         variant_product = VariantProduct.objects.get(id=product_id)
#                         if variant_product.stock >= quantity:
#                             variant_product.stock -= quantity
#                             variant_product.save()  # Update stock
#                         else:
#                             error_message = f"Insufficient stock for variant product {variant_product.product.name}."
#                             return render_error_page(request, error_message, status_code=400)

#                     # If it's a simple product
#                     elif product_type == "simple":
#                         simple_product = SimpleProduct.objects.get(id=product_id)
#                         if simple_product.stock >= quantity:
#                             simple_product.stock -= quantity
#                             simple_product.save()  # Update stock
#                         else:
#                             error_message = f"Insufficient stock for simple product {simple_product.name}."
#                             return render_error_page(request, error_message, status_code=400)

#                 except (VariantProduct.DoesNotExist, SimpleProduct.DoesNotExist):
#                     error_message = f"Product not found with id {product_id}."
#                     return render_error_page(request, error_message, status_code=400)

#                 except (VariantProduct.DoesNotExist, SimpleProduct.DoesNotExist):
#                     error_message = f"Product not found with id {product_id}."
#                     return render_error_page(request, error_message, status_code=400)

#                 # Send confirmation email
#                 context = {
#                     'full_name': user.full_name,
#                     'email': user.email,
#                     'order_value': t_price,
#                     'order_details': ord_meta_data,
#                     'address': selected_address,
#                 }
#                 send_template_email(
#                     subject='Order Confirmation',
#                     template_name='users/email/order_confirmation.html',
#                     context=context,
#                     recipient_list=[user.email]
#                 )

#                 messages.success(request, "Order placed successfully. Cash on Delivery selected.")
#                 cart.delete()
#                 return redirect("app_common:home")

#             else:
#                 error_message = "Invalid payment method."
#                 return render_error_page(request, error_message, status_code=400)

#         except Exception as e:
#             error_message = f"An unexpected error occurred while processing your order: {str(e)}"
#             return render_error_page(request, error_message, status_code=400)
