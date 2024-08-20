from django.views import View
from django.shortcuts import redirect, get_object_or_404,render
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings
from cart.models import Cart
from orders.models import Order
from users.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from cart.serializer import CartSerializer
from payment import razorpay  # Assuming you have a utility function for Razorpay verification
import json

from users.user_views.emails import send_template_email

app = 'payment/'

@method_decorator(csrf_exempt, name='dispatch')
class PaymentSuccess(View):

    model = Order

    def post(self, request):
        user = request.user
        cart = Cart.objects.get(user=user)
        data = json.loads(request.body)
        address_id = data.get('address_id')
        payment_method = data.get('payment_method')  # Get payment method from request

        # Fetch order details
        order_details = CartSerializer(cart).data
        ord_meta_data = {k: v for d in order_details.values() for k, v in d.items()}
        t_price = float(ord_meta_data['final_cart_value'])

        user_addresses = user.address
        selected_address = next((addr for addr in user_addresses if addr['id'] == address_id), None)

        if payment_method == 'razorpay':
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')
            
            if razorpay.verify_signature(data):
                try:
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
                        payment_method='razorpay',
                        payment_status='Paid'  # Set payment status to Paid for Razorpay
                    )
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
                    order.save()
                    messages.success(request, "Order Successful!")
                    cart.delete()
                    return redirect("users:home")
                except Exception as e:
                    messages.error(request, "Error while placing Order.")
                    return redirect("cart:checkout")
            else:
                messages.error(request, "Payment verification failed.")
                return redirect("cart:checkout")

        elif payment_method == 'cod':
            try:
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
                messages.success(request, "Order placed successfully. Cash on Delivery selected.")
                cart.delete()
                return redirect("users:home")
            except Exception as e:
                messages.error(request, "Error while placing Order.")
                return redirect("cart:checkout")
        
        else:
            messages.error(request, "Invalid payment method.")
            return redirect("cart:checkout")



class SuccessPage(View):
    template = app + "payment_success.html"
    def get(self, request):
        return render(request, self.template)