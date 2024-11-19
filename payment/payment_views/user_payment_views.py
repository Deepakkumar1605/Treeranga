from decimal import Decimal
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
from .delhivery_api import create_delhivery_order, cancel_delhivery_order
from users.user_views.emails import send_template_email

app = 'payment/'



class SuccessPage(View):
    template = app + "payment_success.html"

    def get(self, request):
        try:
            return render(request, self.template)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)



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
            
            print(payment_method,"paymentmethod--------------------------")

            # Fetch order details
            order_details = CartSerializer(cart).data
            ord_meta_data = {k: v for d in order_details.values() for k, v in d.items()}
            # print(ord_meta_data,"------")
            ord_meta_data = convert_decimals_to_str(ord_meta_data)  # Convert before using

            # print(f"Order meta data: {ord_meta_data}")
            t_price = float(ord_meta_data.get('final_cart_value', 0))

            user_addresses = user.address  # Assuming user.address returns a list
            selected_address = next((addr for addr in user_addresses if addr['id'] == address_id), None)
            if not selected_address:
                error_message = "Address not found."
                return render_error_page(request, error_message, status_code=400)

            if payment_method == 'prepaid':
                razorpay_payment_id = data.get('razorpay_payment_id')
                razorpay_order_id = data.get('razorpay_order_id')
                razorpay_signature = data.get('razorpay_signature')

                if not verify_signature(data):  # Make sure to implement verify_signature function
                    error_message = "Payment verification failed."
                    return render_error_page(request, error_message, status_code=400)

                try:
                    # Create the order
                    order = self.model(
                        user=user,
                        full_name=cart.user.full_name,
                        email=cart.user.email,
                        products=cart.products,
                        order_value=float(t_price),
                        address=selected_address,
                        order_meta_data=ord_meta_data,
                        razorpay_payment_id=razorpay_payment_id,
                        razorpay_order_id=razorpay_order_id,
                        razorpay_signature=razorpay_signature,
                        payment_method=payment_method,
                        payment_status='paid'
                    )

                    order.save()
                    # # Sample product structure from order.products
                    order_items = []
                    full_address = f"{selected_address.get('Address1', '')} {selected_address.get('Address2', '')}".strip()
                    for product_key, product in order.products.items():
                        item_string = f"name: {product['info']['name']}, sku: {product['info']['sku']}, units: {product['quantity']}, selling_price: {product['info']['discount_price']}, discount: {product['info']['max_price'] - product['info']['discount_price']}, tax: {product['info'].get('tax', '')}, hsn: {product['info'].get('hsn', '')}"

                        order_items.append(item_string)

                    

                    # Prepare and send order creation request to Delhivery
                    delhivery_order_response = create_delhivery_order({
                            "shipments": [
                                {
                                    "name": order.full_name,
                                    "add": full_address,
                                    "pin": selected_address.get('pincode', ''),
                                    "city": selected_address.get('city', ''),
                                    "state": selected_address.get('state', ''),
                                    "country": selected_address.get('country', ''),
                                    "phone": selected_address.get('mobile_no', ''),
                                    "order": str(order.uid),
                                    "payment_mode": payment_method,
                                    "return_pin": "",
                                    "return_city": "",
                                    "return_phone": "",
                                    "return_add": "",
                                    "return_state": "",
                                    "return_country": "",
                                    "products_desc": ', '.join(order_items),
                                    "hsn_code": "",
                                    "cod_amount": float(t_price),
                                    "order_date": "",
                                    "total_amount": "",
                                    "seller_add": "",
                                    "seller_name": "",
                                    "seller_inv": "",
                                    "quantity": "",
                                    "waybill": "",
                                    "shipment_width": "",
                                    "shipment_height": "",
                                    "weight": "",
                                    "seller_gst_tin": "",
                                    "shipping_mode": "Surface",
                                    "address_type": "home"
                                }
                            ],
                            "pickup_location": {
                                "name": "TREERANGA",
                                "add": "badambadi",
                                "city": "jajpur",
                                "pin_code": "755043",
                                "country": "India",
                                "phone": "8310418179"
                            }
                        
                    })

                    # Handle the response from Delhivery
                    if delhivery_order_response:
                        print(f"Delhivery order created with waybill: {delhivery_order_response}")
                    else:
                        print("Delhivery order creation failed.")
                    

                except Exception as e:
                    print(e)
                    error_message = "Error creating order: {}".format(str(e))
                    return render_error_page(request, error_message, status_code=500)

                # Reduce stock for each product in the cart
                self.reduce_stock(cart)

                # Send confirmation email
                self.send_confirmation_email(user, t_price, ord_meta_data, selected_address)

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
                    order_value=float(t_price),
                    address=selected_address,
                    order_meta_data=ord_meta_data,
                    payment_method='cod',
                    payment_status='Pending'  # Set payment status to Pending for COD
                )
                order.save()
                
               # Sample product structure from order.products
                order_items = []
                full_address = f"{selected_address.get('Address1', '')} {selected_address.get('Address2', '')}".strip()
                for product_key, product in order.products.items():
                    item_string = f"name: {product['info']['name']}, sku: {product['info']['sku']}, units: {product['quantity']}, selling_price: {product['info']['discount_price']}, discount: {product['info']['max_price'] - product['info']['discount_price']}, tax: {product['info'].get('tax', '')}, hsn: {product['info'].get('hsn', '')}"

                    order_items.append(item_string)
                
                #Prepare and send order creation request to Delhivery
                delhivery_order_response = create_delhivery_order({
                        "shipments": [
                            {
                                "name": order.full_name,
                                "add": full_address,
                                "pin": selected_address.get('pincode', ''),
                                "city": selected_address.get('city', ''),
                                "state": selected_address.get('state', ''),
                                "country": selected_address.get('country', ''),
                                "phone": selected_address.get('mobile_no', ''),
                                "order": str(order.uid),
                                "payment_mode": payment_method,
                                "return_pin": "",
                                "return_city": "",
                                "return_phone": "",
                                "return_add": "",
                                "return_state": "",
                                "return_country": "",
                                "products_desc": ', '.join(order_items),
                                "hsn_code": "",
                                "cod_amount": float(t_price),
                                "order_date": "",
                                "total_amount": "",
                                "seller_add": "",
                                "seller_name": "",
                                "seller_inv": "",
                                "quantity": "",
                                "waybill": "",
                                "shipment_width": "",
                                "shipment_height": "",
                                "weight": "",
                                "seller_gst_tin": "",
                                "shipping_mode": "Surface",
                                "address_type": "home"
                            }
                        ],
                        "pickup_location": {
                            "name": "TREERANGA",
                            "add": "badambadi",
                            "city": "jajpur",
                            "pin_code": "755043",
                            "country": "India",
                            "phone": "8310418179"
                        }
                    
                })

                # Handle the response from Delhivery
                if delhivery_order_response:
                    print(f"Delhivery order created with waybill: {delhivery_order_response}")
                else:
                    print("Delhivery order creation failed.")



                # Reduce stock for each product in the cart
                self.reduce_stock(cart)

                # Send confirmation email
                self.send_confirmation_email(user, t_price, ord_meta_data, selected_address)

                messages.success(request, "Order placed successfully. Cash on Delivery selected.")
                cart.delete()
                return redirect("app_common:home")

            else:
                error_message = "Invalid payment method."
                return render_error_page(request, error_message, status_code=400)

        except Exception as e:
            error_message = f"An unexpected error occurred while processing your order: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def reduce_stock(self, cart):
        """Reduces stock for each product in the cart."""
        for product_key, product_data in cart.products.items():
            product_id = product_data['info']['product_id']  # This ID can be for either simple or variant product
            quantity = product_data['quantity']
            product_type = product_data['info']['variant']  # Fetch product type directly from the data

            try:
                # If it's a variant product
                if product_type == "yes":
                    variant_product = VariantProduct.objects.get(id=product_id)
                    if variant_product.stock >= quantity:
                        variant_product.stock -= quantity
                        variant_product.save()  # Update stock
                    else:
                        raise Exception(f"Insufficient stock for variant product {variant_product.product.name}.")

                # If it's a simple product
                elif product_type == "no":
                    simple_product = SimpleProduct.objects.get(id=product_id)
                    if simple_product.stock >= quantity:
                        simple_product.stock -= quantity
                        simple_product.save()  # Update stock
                    else:
                        raise Exception(f"Insufficient stock for simple product {simple_product.name}.")

            except (VariantProduct.DoesNotExist, SimpleProduct.DoesNotExist):
                raise Exception(f"Product not found with id {product_id}.")

    def send_confirmation_email(self, user, t_price, ord_meta_data, selected_address):
        """Sends confirmation email after order placement."""
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

def convert_decimals_to_str(data):
    if isinstance(data, dict):
        return {k: convert_decimals_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimals_to_str(v) for v in data]
    elif isinstance(data, Decimal):
        return str(data)
    return data


class CancelOrderView(View):
    def post(self, request):
        waybill = request.POST.get('waybill')  # Get waybill from the request
        if not waybill:
            return JsonResponse({"success": False, "message": "Waybill is required."})

        result = cancel_delhivery_order(waybill)
        return JsonResponse(result)