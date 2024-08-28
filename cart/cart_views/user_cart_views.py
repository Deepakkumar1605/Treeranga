
from django.shortcuts import get_object_or_404, redirect,render
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from product.models import DeliverySettings, Products, SimpleProduct, Category
from orders.models import Order
from cart.models import Cart
from cart.serializer import CartSerializer,DirectBuySerializer
from decimal import Decimal, InvalidOperation,ROUND_HALF_UP
from uuid import uuid4
from payment import razorpay

class ShowCart(View):
    def get(self, request):
        # Get categories for the view
        category_obj = Category.objects.all()

        # Get user and cart items
        user = request.user
        if user.is_authenticated:
            cart_items = Cart.objects.filter(user=user).first()
            products = cart_items.products if cart_items and cart_items.products else {}
        else:
            cart_items = None
            products = request.session.get('cart', {}).get('products', {})

        # Fetch delivery settings
        delivery_settings = DeliverySettings.objects.first()
        delivery_charge_per_bag = delivery_settings.delivery_charge_per_bag
        delivery_free_order_amount = delivery_settings.delivery_free_order_amount 

        total_original_price = Decimal('0.00')
        total_price = Decimal('0.00')
        delivery = Decimal('0.00')
        final_cart_value = Decimal('0.00')
        has_flat_delivery_product = False
        has_non_flat_delivery_product = False

        for product_key, product_info in products.items():
            max_price = Decimal(product_info['info'].get('max_price', '0.00'))
            discount_price = Decimal(product_info['info'].get('discount_price', '0.00'))
            quantity = product_info.get('quantity', 0)

            total_original_price += max_price * quantity
            total_price += discount_price * quantity

            product_id = product_info['info'].get('product_id')
            if product_id:
                try:
                    simple_product = SimpleProduct.objects.get(product=product_id)
                    if simple_product.virtual_product:
                        # Product is virtual; no delivery fee
                        has_flat_delivery_product = True
                    elif simple_product.flat_delivery_fee:
                        # Product has a flat delivery fee; set flag
                        has_flat_delivery_product = True
                    else:
                        # Product is a normal product; requires delivery fee
                        has_non_flat_delivery_product = True
                except SimpleProduct.DoesNotExist:
                    pass

        if total_price > 0:
            final_cart_value = total_price
            discount_price = total_original_price - total_price

            if has_flat_delivery_product and not has_non_flat_delivery_product:
                # All products are virtual or have flat delivery fee, so no delivery charge
                delivery = Decimal('0.00')
            elif final_cart_value < delivery_free_order_amount:
                # Normal delivery charge applies
                delivery = delivery_charge_per_bag
            final_cart_value += delivery
        else:
            discount_price = Decimal('0.00')

        if user.is_authenticated and cart_items:
            cart_items.total_price = float(total_price)
            cart_items.save()
        print(products)
        context = {
            'category_obj': category_obj,
            'cartItems': cart_items,
            'products': products,
            'totaloriginalprice': float(total_original_price),
            'totalPrice': float(total_price),
            'Delivery': float(delivery),
            'final_cart_value': float(final_cart_value),
            'discount_price': float(discount_price),
            'MEDIA_URL': settings.MEDIA_URL,
        }

        return render(request, "cart/user/cartpage.html", context)


class AddToCartView(View):
    def get(self, request, product_id):
        try:
            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user)
                is_user_authenticated = True
            else:
                cart = request.session.get('cart', {'products': {}})
                is_user_authenticated = False

            product_obj = get_object_or_404(SimpleProduct, id=product_id)
            quantity = int(request.GET.get('quantity', 1))
            
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
                'product_id': product_obj.product.id,
                'uid': product_uid,
                'name': product_obj.product.name,
                'image': product_obj.product.image.url if product_obj.product.image else None,
                'max_price': product_obj.product_max_price,
                'discount_price': product_obj.product_discount_price,
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

            if is_user_authenticated:
                cart.products = products
                cart.total_price = sum(item['total_price'] for item in products.values())
                cart.save()
            else:
                cart['products'] = products
                cart['total_price'] = sum(item['total_price'] for item in products.values())
                request.session['cart'] = cart
                request.session.modified = True

            messages.success(request, f"{product_obj.product.name} added to cart.")
            return redirect("users:home")
        except Exception as e:
            print(f"Add to cart error: {e}")
            return HttpResponse(f"An error occurred: {e}", status=500)




class ManageCart(View):
    def get(self, request, c_p_uid):
        operation_type = request.GET.get('operation')

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

        if request.user.is_authenticated:
            cart.products = products
            cart.total_price = sum(item['total_price'] for item in products.values())
            cart.save()
        else:
            cart['products'] = products
            cart['total_price'] = sum(item['total_price'] for item in products.values())
            request.session['cart'] = cart
            request.session.modified = True

        return redirect('cart:showcart')



def RemoveFromCart(request, cp_uid):
    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
        if cp_uid in cart.products:
            cart.products.pop(cp_uid)
            cart.total_price = sum(item['total_price'] for item in cart.products.values())
            cart.save()
    else:
        cart = request.session.get('cart', {'products': {}})
        products = cart.get('products', {})
        if cp_uid in products:
            products.pop(cp_uid)
            cart['total_price'] = sum(item['total_price'] for item in products.values())
            cart['products'] = products
            request.session['cart'] = cart
            request.session.modified = True

    return redirect("cart:showcart")




@method_decorator(login_required(login_url='users:login'), name='dispatch')
class Checkout(View):
    template = "cart/user/checkout.html"
    model = Order

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('users:login')}?next={request.path}")

        user = request.user

        try:
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

                # Update the total price in the user cart
                user_cart.products = user_cart_products
                user_cart.total_price = sum(item['total_price'] for item in user_cart_products.values())
                user_cart.save()

                # Clear session cart after merging
                request.session.pop('cart', None)

            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return redirect("cart:showcart")
        except Exception as e:
            print(f"Error in checkout process: {e}")
            return redirect("cart:showcart")

        # Serialize cart details
        order_details = CartSerializer(cart).data
        totaloriginalprice = 0
        totalPrice = 0
        GST = 0
        Delivery = 0
        final_cart_value = 0
        addresses = user.address or []

        # Razorpay order creation
        status, rz_order_id = razorpay.create_order_in_razPay(
            amount=int(float(order_details['products_data']['final_cart_value']) * 100)  # Amount in paise
        )

        for i, j in order_details.items():
            totaloriginalprice = Decimal(j['gross_cart_value'])
            totalPrice = Decimal(j['our_price'])
            Delivery = Decimal(j['charges']['Delivery'])
            final_cart_value = j['final_cart_value']

        discount_price = totaloriginalprice - totalPrice

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



@method_decorator(login_required(login_url='users:login'), name='dispatch')
class DirectBuyCheckout(View):
    template = "cart/user/directbuycheckout.html"  # Update with your actual template path

    def get(self, request, p_id):
        user = request.user
        product = get_object_or_404(Products, id=p_id)
        product_uid = product.uid

        our_price = 0
        totaloriginalprice = 0
        GST = 0
        Delivery = 0
        final_value = 0
        discount_amount = 0

        order_details = DirectBuySerializer(product).data
        
        for i, j in order_details.items():
            totaloriginalprice = Decimal(j['gross_value'])
            our_price = Decimal(j['our_price'])
            GST = Decimal(j['charges']['GST'])
            Delivery = Decimal(j['charges']['Delivery'])
            final_value = j['final_value']
            discount_amount = j['discount_amount']

        addresses = user.address or []
        # Commented out Razorpay fields for now
        # status, rz_order_id = rozerpay.create_order_in_razPay(amount=int(float(final_value)))

        context = {
            'p_id': p_id,
            'our_price': our_price,
            'totaloriginalprice': totaloriginalprice,
            "total_price": final_value,
            'GST': GST,
            'Delivery': Delivery,
            'discount_amount': discount_amount,
            "MEDIA_URL": settings.MEDIA_URL,
            # "rz_order_id": rz_order_id,
            # "api_key": settings.RAZORPAY_API_KEY,
            "product_uid": product_uid,
            "addresses": addresses,
        }

        return render(request, self.template, context)

    def post(self, request):
        p_id = request.POST['product_id']
        url = reverse('cart:directbuycheckout', args=[p_id])

        return HttpResponseRedirect(url)






# checkout address

class AddAddress(View):
    def post(self, request):
        if request.method == 'POST':
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
        else:
            return redirect('users:home')




def update_address_view(request):
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

        try:
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

            # Save the updated addresses back to the user model
            user_obj.address = addresses
            user_obj.save()
            messages.success(request, 'Address updated successfully.')

            # Redirect to the checkout page
            return redirect('cart:checkout')

        except Exception as e:
            messages.error(request, f'Failed to update address: {str(e)}')
            return redirect('app_commo:home')
    else:
        return redirect('app_common:home')




class DeleteAddress(View):
    def get(self, request, address_id):
        user = request.user
        addresses = user.address or []

        # Remove the address with the specified ID
        addresses = [address for address in addresses if address.get('id') != address_id]

        # Save the updated list of addresses back to the user model
        user.address = addresses
        user.save()

        # Redirect to the checkout page
        return redirect('cart:checkout')



def transfer_session_cart_to_user(request, user):
    session_cart = request.session.get('cart', {}).get('products', {})
    if session_cart:
        try:
            user_cart, created = Cart.objects.get_or_create(user=user)
            user_cart_products = user_cart.products or {}

            for product_key, product_info in session_cart.items():
                if product_key in user_cart_products:
                    user_cart_products[product_key]['quantity'] += product_info['quantity']
                else:
                    user_cart_products[product_key] = product_info

            user_cart.products = user_cart_products
            user_cart.total_price = sum(item['total_price'] for item in user_cart_products.values())
            user_cart.save()
            request.session.pop('cart', None)
            request.session.modified = True
        except Exception as e:
            print(f"Error transferring session cart: {e}")
            messages.error(request, "There was an issue transferring your cart items.")
