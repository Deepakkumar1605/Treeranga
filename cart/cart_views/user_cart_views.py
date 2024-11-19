
from datetime import timezone
import json
from django.shortcuts import get_object_or_404, redirect,render
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from app_common.error import render_error_page
from coupons.models import Coupon
from users.models import User
from product.models import DeliverySettings, Products, SimpleProduct, Category
from orders.models import Order
from cart.models import Cart
from cart.serializer import CartSerializer
from decimal import Decimal, InvalidOperation,ROUND_HALF_UP
from uuid import uuid4
from payment import razorpay
from product_variations.models import VariantProduct
from django.utils import timezone

from payment.payment_views.delhivery_api import check_pincode_serviceability

class ShowCart(View):
    def get(self, request):

        category_obj = Category.objects.all()
        user = request.user

        cupon_discounted_amount = Decimal('0.00')
        coupons = Coupon.objects.filter(is_active=True)  # Fetch all active coupons

        if user.is_authenticated:
            cart_items = Cart.objects.filter(user=user).first()
            if cart_items:
                products = cart_items.products if hasattr(cart_items, 'products') else {}
                final_cart_value = cart_items.total_price if cart_items else Decimal('0.00')
                discount_amount = cart_items.coupon_discount_amount if cart_items else Decimal('0.00')
                applied_coupon = cart_items.applied_coupon if cart_items else None
                cupon_discounted_amount += discount_amount

                # Set coupon values if there are no products
                if not products:
                    applied_coupon = None
                    cupon_discounted_amount = Decimal('0.00')
            else:
                products = {}
                final_cart_value = Decimal('0.00')
                discount_amount = Decimal('0.00')
                applied_coupon = None
                cupon_discounted_amount = Decimal('0.00')
        else:
            products = request.session.get('cart', {}).get('products', {})
            final_cart_value = Decimal(request.session.get('total_price', '0.00'))
            discount_amount = Decimal(request.session.get('coupon_discount_amount', '0.00'))
            applied_coupon = request.session.get('applied_coupon', None)
            cupon_discounted_amount += discount_amount

            # Set coupon values if there are no products
            if not products:
                applied_coupon = None
                cupon_discounted_amount = Decimal('0.00')

        # Initialize totals
        total_original_price = Decimal('0.00')
        total_price = Decimal('0.00')
        total_discounted_amount = Decimal('0.00')

        # Calculate total price
        for product_key, product_info in products.items():
            max_price = Decimal(product_info['info'].get('max_price', '0.00'))
            discount_price = Decimal(product_info['info'].get('discount_price', '0.00'))
            quantity = product_info.get('quantity', 0)
            total_original_price += max_price * quantity
            total_price += discount_price * quantity
            total_discounted_amount += (max_price - discount_price) * quantity

        # Apply coupon discount to the total price
        final_total_price = (total_price - cupon_discounted_amount).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

        # Prepare context
        context = {
            'category_obj': category_obj,
            'products': products,
            'totaloriginalprice': float(total_original_price),
            'totalPrice': float(total_price),  # Use the rounded final total price
            'final_cart_value': float(final_total_price),  # Include delivery in final cart value
            'discount_price': float(total_discounted_amount),
            'cupon_discounted_ammount': float(cupon_discounted_amount),
            'applied_coupon': applied_coupon,
            'coupons': coupons,  # Pass available coupons to the context
            'MEDIA_URL': settings.MEDIA_URL,
        }

        return render(request, "cart/user/cartpage.html", context)




class AddToCartView(View):
    def get(self, request, product_id):
        quantity = int(request.GET.get('quantity', 1))
        variant = request.GET.get('variant', '')

        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            is_user_authenticated = True
        else:
            cart = request.session.get('cart', {'products': {}})
            is_user_authenticated = False

        # Get the product object based on the variant
        if variant == "yes":
            product_obj = get_object_or_404(VariantProduct, id=product_id)
        else:
            product_obj = get_object_or_404(SimpleProduct, id=product_id)

        # Ensure quantity is within valid range
        if quantity <= 0:
            messages.error(request, "Quantity must be at least 1.")
            return redirect(request.META.get('HTTP_REFERER'))
        elif quantity > 6:
            quantity = 6
            messages.warning(request, "Maximum quantity allowed is 6. Adjusting quantity to 6.")

        product_uid = product_obj.product.uid or f"{product_obj.product.name}_{product_obj.id}"
        product_key = str(product_obj.id)
        product_info = {
            'product_id': product_obj.id,
            'sku':product_obj.product.sku_no,
            'uid': product_uid,
            'name': product_obj.product.name,
            'image': product_obj.product.image.url if product_obj.product.image else None,
            'max_price': product_obj.product_max_price,
            'discount_price': product_obj.product_discount_price,
            'variant': variant,
        }

        products = cart.products if is_user_authenticated else cart.get('products', {})

        if product_key in products:
            new_quantity = products[product_key]['quantity'] + quantity
            if new_quantity > 6:
                quantity = 6 - products[product_key]['quantity']
                messages.warning(request, "Adding more items would exceed the maximum limit. Adjusting quantity accordingly.")
            products[product_key]['quantity'] += quantity
            products[product_key]['total_price'] = products[product_key]['quantity'] * product_obj.product_discount_price
        else:
            products[product_key] = {
                'info': product_info,
                'quantity': quantity,
                'total_price': quantity * product_obj.product_discount_price
            }

        # Update total price and reset any applied coupon
        total_price = sum(item['total_price'] for item in products.values())
        if is_user_authenticated:
            cart.products = products
            cart.total_price = total_price
            cart.applied_coupon = None  # Reset coupon
            cart.coupon_discount_amount = Decimal('0.00')  # Reset discount amount
            cart.save()
        else:
            cart['products'] = products
            cart['total_price'] = total_price
            request.session['total_price'] = total_price
            request.session['applied_coupon'] = None  # Reset coupon in session
            request.session['coupon_discount_amount'] = '0.00'  # Reset discount amount in session
            request.session['cart'] = cart
            request.session.modified = True

        messages.success(request, f"{product_obj.product.name} added to cart.")
        return redirect("app_common:home")



class ManageCart(View):
    def get(self, request, c_p_uid):
        operation_type = request.GET.get('operation')

        try:
            if request.user.is_authenticated:
                cart = Cart.objects.get(user=request.user)
                products = cart.products or {}
            else:
                cart = request.session.get('cart', {'products': {}})
                products = cart.get('products', {})

            product_found = False
            max_quantity = 6  # Define the maximum quantity allowed

            for product_key, product_info in products.items():
                if c_p_uid == product_info['info']['uid']:
                    product_found = True
                    if operation_type == 'plus':
                        if product_info['quantity'] < max_quantity:
                            product_info['quantity'] += 1
                            product_info['total_price'] += product_info['info']['discount_price']
                        else:
                            return HttpResponse(f"Cannot add more than {max_quantity} of this product.", status=400)
                    elif operation_type == 'min':
                        if product_info['quantity'] > 1:
                            product_info['quantity'] -= 1
                            product_info['total_price'] -= product_info['info']['discount_price']
                        else:
                            products.pop(product_key)
                    break

            if not product_found:
                return HttpResponse(f"Product with UID {c_p_uid} not found in cart.", status=404)

            # Reset coupon info when modifying the cart
            if request.user.is_authenticated:
                cart.applied_coupon = None
                cart.coupon_discount_amount = Decimal('0.00')
                cart.products = products
                cart.total_price = sum(item['total_price'] for item in products.values())
                cart.save()
            else:
                cart['applied_coupon'] = None
                cart['coupon_discount_amount'] = '0.00'
                cart['products'] = products
                cart['total_price'] = sum(item['total_price'] for item in products.values())
                request.session['cart'] = cart
                request.session.modified = True

            return redirect('cart:showcart')

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)



def RemoveFromCart(request, cp_uid):
    try:
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
            if cp_uid in cart.products:
                cart.products.pop(cp_uid)
                cart.total_price = sum(item['total_price'] for item in cart.products.values())
                # Reset coupon info when removing a product
                cart.applied_coupon = None
                cart.coupon_discount_amount = Decimal('0.00')
                cart.save()
        else:
            cart = request.session.get('cart', {'products': {}})
            products = cart.get('products', {})
            if cp_uid in products:
                products.pop(cp_uid)
                cart['total_price'] = sum(item['total_price'] for item in products.values())
                cart['products'] = products
                # Reset coupon info when removing a product
                cart['applied_coupon'] = None
                cart['coupon_discount_amount'] = '0.00'
                request.session['cart'] = cart
                request.session.modified = True

        return redirect("cart:showcart")

    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        return render_error_page(request, error_message, status_code=400)



def cart_count_processor(request):
    try:
        cart_count = 0
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
            if cart and cart.products:
                cart_count = len(cart.products)
        else:
            cart = request.session.get('cart', {})
            if cart and 'products' in cart:
                cart_products = cart.get('products', {})
                cart_count = len(cart_products)
                
        return {'cart_count': cart_count}

    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        return render_error_page(request, error_message, status_code=400)



@method_decorator(login_required(login_url='users:login'), name='dispatch')
class Checkout(View):
    template = "cart/user/checkout.html"
    model = Order

    def get(self, request):
        try:
            user = request.user

            # Merge session cart with user cart if available
            session_cart = request.session.get('cart', {}).get('products', {})
            if session_cart:
                user_cart, created = Cart.objects.get_or_create(user=user)
                user_cart_products = user_cart.products or {}

                for key, value in session_cart.items():
                    if key in user_cart_products:
                        user_cart_products[key]['quantity'] += value['quantity']
                    else:
                        user_cart_products[key] = value

                user_cart.products = user_cart_products
                user_cart.total_price = sum(
                    Decimal(item['product_discount_price']) * item['quantity'] 
                    for item in user_cart_products.values()
                )
                user_cart.save()
                request.session.pop('cart', None)

            cart = Cart.objects.get(user=user)
            order_details = CartSerializer(cart).data
            print(f"Order Details : {order_details}")
            # Extract necessary details
            final_cart_value = Decimal(order_details['products_data']['final_cart_value'])
            totaloriginalprice = Decimal(order_details['products_data']['gross_cart_value'])
            totalPrice = Decimal(order_details['products_data']['our_price'])
            Delivery = Decimal(order_details['products_data']['charges']['Delivery'])
            discount_price = totaloriginalprice - totalPrice
            addresses = user.address or []

            # Razorpay order creation
            status, rz_order_id = razorpay.create_order_in_razPay(
                amount=int(final_cart_value * 100)
            )

            context = {
                "cart": cart.products,
                "rz_order_id": rz_order_id,
                "api_key": settings.RAZORPAY_API_KEY,
                "addresses": addresses,
                'totaloriginalprice': totaloriginalprice,
                'totalPrice': totalPrice,
                'Delivery': Delivery,
                'final_cart_value': final_cart_value,
                'discount_price': discount_price,
                "MEDIA_URL": settings.MEDIA_URL
            }
            return render(request, self.template, context)

        except Cart.DoesNotExist:
            return redirect("cart:showcart")
        except Exception as e:
            error_message = f"An unexpected error occurred during checkout: {str(e)}"
            return render_error_page(request, error_message, status_code=400)



# checkout address

class AddAddress(View):
    def post(self, request):
        try:
            Address1 = request.POST["Address1"]
            Address2 = request.POST["Address2"]
            country = request.POST["country"]
            state = request.POST["state"]
            city = request.POST["city"]
            mobile_no = request.POST["mobile_no"]
            pincode = request.POST["pincode"]

            address_id = str(uuid4())
            address_data = {
                "id": address_id,
                "Address1": Address1,
                "Address2": Address2,
                "country": country,
                "state": state,
                "city": city,
                "mobile_no": mobile_no,
                "pincode": pincode,
            }

            user = request.user
            addresses = user.address or []
            addresses.append(address_data)
            user.address = addresses
            user.save()

            return redirect('cart:checkout')

        except Exception as e:
            error_message = f"An unexpected error occurred while adding address: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


def update_address_view(request):
    try:
        if request.method == 'POST':
            user = request.user
            user_obj = get_object_or_404(User, id=user.id)
            a_id = request.POST.get('a_id')
            Address1 = request.POST.get('Address1')
            Address2 = request.POST.get('Address2')
            country = request.POST.get('country')
            state = request.POST.get('state')
            city = request.POST.get('city')
            mobile_no = request.POST.get('mobile_no')
            pincode = request.POST.get('pincode')

            addresses = user_obj.address or []

            # Find and update the address with the specified id
            for address in addresses:
                if address['id'] == a_id:
                    address.update({
                        'Address1': Address1,
                        'Address2': Address2,
                        'country': country,
                        'state': state,
                        'city': city,
                        'mobile_no': mobile_no,
                        'pincode': pincode,
                    })
                    break

            user_obj.address = addresses
            user_obj.save()
            messages.success(request, 'Address updated successfully.')

            return redirect('cart:checkout')

    except Exception as e:
        error_message = f"Failed to update address: {str(e)}"
        return render_error_page(request, error_message, status_code=400)

class DeleteAddress(View):
    def get(self, request, address_id):
        try:
            user = request.user
            addresses = user.address or []

            # Remove the address with the specified ID
            addresses = [address for address in addresses if address.get('id') != address_id]

            # Save the updated list of addresses back to the user model
            user.address = addresses
            user.save()

            return redirect('cart:checkout')

        except Exception as e:
            error_message = f"An unexpected error occurred while deleting address: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

def transfer_session_cart_to_user(request, user):
    session_cart = request.session.get('cart', {})
    session_cart_products = session_cart.get('products', {})
    
    if session_cart_products:
        try:
            user_cart, created = Cart.objects.get_or_create(user=user)
            user_cart_products = user_cart.products or {}

            for product_key, product_info in session_cart_products.items():
                if product_key in user_cart_products:
                    user_cart_products[product_key]['quantity'] += product_info['quantity']
                else:
                    user_cart_products[product_key] = product_info

            user_cart.products = user_cart_products
            
            # Calculate total price using original prices
            user_cart.total_price = sum(item['info']['discount_price'] * item['quantity'] for item in user_cart_products.values())

            # Reset applied coupon and discount amount
            user_cart.applied_coupon = None
            user_cart.coupon_discount_amount = Decimal('0.00')

            user_cart.save()

            # Clear session cart
            request.session.pop('cart', None)
            request.session.modified = True

        except Exception as e:
            error_message = f"Error transferring session cart: {str(e)}"
            messages.error(request, error_message)

            
class ApplyCouponView(View):
    def post(self, request):
        try:
            # Get the coupon code from the request body (JSON format)
            data = json.loads(request.body)
            coupon_code = data.get('coupon_code')

            # Validate if the coupon exists and is active
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                
                # Ensure the coupon is within its valid date range
                if coupon.valid_from <= timezone.now() <= coupon.valid_to:
                    if request.user.is_authenticated:
                        # Get the user's cart
                        cart = Cart.objects.filter(user=request.user).first()

                        if cart and cart.total_price > 0:
                            # Apply the coupon to the cart
                            discount_price = self.calculate_coupon_discount(coupon, cart.total_price)
                            print(discount_price,"Dis")
                            print(type(discount_price),type(cart.total_price))
                            final_price = cart.total_price - float(discount_price)
                            cart.applied_coupon = coupon
                            cart.total_price = float(round(final_price, 2))
                            cart.coupon_discount_amount = discount_price
                            print(cart.total_price,"after_cupon")
                            cart.save()

                            return JsonResponse({
                                'success': True, 
                                'final_price': float(final_price),
                                'discount_price': float(discount_price),
                                'message': 'Coupon applied successfully!'
                            })
                        else:
                            return JsonResponse({'success': False, 'message': 'No items in the cart.'})

                    else:
                        # For unauthenticated users, apply the coupon via session
                        cart_session = request.session.get('cart', {})
                        total_price = Decimal(cart_session.get('total_price', '0.00'))

                        if total_price > 0:
                            discount_price = self.calculate_coupon_discount(coupon, total_price)
                            final_price = total_price - discount_price

                            # Update the session with the applied coupon and final price
                            request.session['applied_coupon'] = coupon.code
                            request.session['total_price'] = float(final_price)
                            request.session['coupon_discount_amount'] = float(discount_price)
                            request.session.modified = True

                            return JsonResponse({
                                'success': True,
                                'final_price': float(final_price),
                                'discount_price': float(discount_price),
                                'message': 'Coupon applied successfully!'
                            })
                        else:
                            return JsonResponse({'success': False, 'message': 'No items in the cart.'})

                else:
                    return JsonResponse({'success': False, 'message': 'Coupon is expired or not valid right now.'})

            except Coupon.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request format.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Something went wrong: {str(e)}'})

    def calculate_coupon_discount(self, coupon, total_price):
        """
        Calculate the discount based on the coupon type.
        """
        discount_price = Decimal('0.00')
        if coupon.discount_type == 'fixed':
            discount_price = Decimal(coupon.discount_value)
        elif coupon.discount_type == 'percent':
            print(total_price,coupon,type(coupon),coupon.discount_value)
            discount_price = Decimal(total_price) * (Decimal(coupon.discount_value) / Decimal('100'))
        
        return discount_price


    
def remove_coupon(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart and cart.applied_coupon:
            cart.total_price = float(round(cart.total_price + float(cart.coupon_discount_amount),2))
            cart.applied_coupon = None
            cart.coupon_discount_amount = 0
            print(cart.total_price,"cp")
            cart.save()
            messages.success(request, 'Coupon removed successfully.')
        else:
            messages.error(request, 'No coupon applied to remove.')
        return redirect('cart:showcart')  
    else:
        # Remove coupon from session for non-authenticated users
        if 'applied_coupon' in request.session:
            final_cart_value = Decimal(request.session.get('total_price', '0.00'))
            discount_amount = Decimal(request.session.get('coupon_discount_amount', '0.00'))
            applied_coupon = request.session.get('applied_coupon', None)
            request.session['total_price'] = float(round(final_cart_value + discount_amount,2))
            request.session['coupon_discount_amount'] = float(0.00)
            request.session.modified = True
            del request.session['applied_coupon']
            messages.success(request, 'Coupon removed successfully.')
        else:
            messages.error(request, 'No coupon applied to remove.')
        return redirect('cart:showcart')
        

