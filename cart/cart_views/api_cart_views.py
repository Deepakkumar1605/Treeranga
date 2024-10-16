from django.utils import timezone
from uuid import uuid4
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from cart import models
from cart import serializer
from django.conf import settings
from decimal import Decimal
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from payment import razorpay

from coupons.models import Coupon
from payment.razorpay import create_order_in_razPay
from product.models import Category, SimpleProduct
from product_variations.models import VariantProduct
from users.serializers import AddressSerializer

class ShowCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Show cart",
        responses={
            200: 'Successfully show cart',
            401: 'Unauthorized',
            404: 'Category not found'
        }
    )
    def get(self, request):
        user = request.user
        cupon_discounted_amount = Decimal('0.00')

        if user.is_authenticated:
            cart_items = models.Cart.objects.filter(user=user).first()
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

        # Serialize the coupon object if it exists
        applied_coupon_data = None
        if applied_coupon:
            applied_coupon_data = {
                'code': applied_coupon.code,
                'discount': float(applied_coupon.discount_value ),
                'valid_from': applied_coupon.valid_from.strftime('%Y-%m-%d'),
                'valid_to': applied_coupon.valid_to.strftime('%Y-%m-%d'),
            }

        # Prepare the data for the response
        response_data = {
            'products': products,
            'total_original_price': float(total_original_price),
            'total_price': float(total_price) - float(cupon_discounted_amount),
            'final_cart_value': float(total_price) - float(cupon_discounted_amount),  # Final price including any discounts
            'discount_price': float(total_discounted_amount),
            'cupon_discounted_amount': float(cupon_discounted_amount),
            'applied_coupon': applied_coupon_data,  # Return the serialized coupon data
            'MEDIA_URL': settings.MEDIA_URL,
        }

        return Response(response_data)


class AddToCartAPIView(APIView):
    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Add product to cart",
        responses={
            200: 'Product added to cart successfully',
            401: 'Unauthorized',
            404: 'Product not found',
            500: 'Internal server error',
        }
    )
    def get(self, request, product_id):
        quantity = int(request.GET.get('quantity', 1))
        variant = request.GET.get('variant', '')

        try:
            # Check if user is authenticated
            if request.user.is_authenticated:
                cart, _ = models.Cart.objects.get_or_create(user=request.user)
                is_user_authenticated = True
            else:
                cart = request.session.get('cart', {'products': {}})
                is_user_authenticated = False

            # Fetch product based on the variant
            if variant == "yes":
                product_obj = get_object_or_404(VariantProduct, id=product_id)
            else:
                product_obj = get_object_or_404(SimpleProduct, id=product_id)

            # Ensure valid quantity
            if quantity <= 0:
                return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)
            elif quantity > 6:
                quantity = 6
                return Response({"warning": "Maximum quantity allowed is 6. Adjusting quantity to 6."}, status=status.HTTP_200_OK)

            product_uid = product_obj.product.uid or f"{product_obj.product.name}_{product_obj.id}"
            product_key = str(product_obj.id)
            product_info = {
                'product_id': product_obj.product.id,
                'uid': product_uid,
                'name': product_obj.product.name,
                'image': product_obj.product.image.url if product_obj.product.image else None,
                'max_price': product_obj.product_max_price,
                'discount_price': product_obj.product_discount_price,
                'variant': variant,
            }

            # Handle cart logic for authenticated and guest users
            products = cart.products if is_user_authenticated else cart.get('products', {})

            if product_key in products:
                new_quantity = products[product_key]['quantity'] + quantity
                if new_quantity > 6:
                    quantity = 6 - products[product_key]['quantity']
                    return Response({"warning": "Adding more items would exceed the maximum limit. Adjusting quantity accordingly."}, status=status.HTTP_200_OK)
                products[product_key]['quantity'] += quantity
                products[product_key]['total_price'] = products[product_key]['quantity'] * product_obj.product_discount_price
            else:
                products[product_key] = {
                    'info': product_info,
                    'quantity': quantity,
                    'total_price': quantity * product_obj.product_discount_price
                }

            # Save the cart for authenticated users or update the session for guest users
            if is_user_authenticated:
                cart.products = products
                cart.total_price = sum(item['total_price'] for item in products.values())
                cart.save()
            else:
                cart['products'] = products
                cart['total_price'] = sum(item['total_price'] for item in products.values())
                request.session['cart'] = cart
                request.session.modified = True

            return Response({"success": f"{product_obj.product.name} added to cart.", "cart": products}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"An error occurred: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ManageCartAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only for authenticated users, change if required.
    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Manage cart operations like adding or removing products from the cart based on UID.",
        responses={
            200: "Cart updated successfully",
            400: "Cannot add more than the maximum allowed quantity",
            404: "Cart or Product not found"
        }
    )
    def get(self, request, c_p_uid):
        operation_type = request.GET.get('operation')

        try:
            if request.user.is_authenticated:
                cart = get_object_or_404(models.Cart, user=request.user)
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
                            return Response(
                                {"detail": f"Cannot add more than {max_quantity} of this product."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    elif operation_type == 'min':
                        if product_info['quantity'] > 1:
                            product_info['quantity'] -= 1
                            product_info['total_price'] -= product_info['info']['discount_price']
                        else:
                            products.pop(product_key)
                    break

            if not product_found:
                return Response(
                    {"detail": f"Product with UID {c_p_uid} not found in cart."},
                    status=status.HTTP_404_NOT_FOUND
                )

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

            return Response(
                {"detail": "Cart updated successfully.", "cart": cart.products},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
           

class RemoveFromCartAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Apply this only if you want it for authenticated users
    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Remove a product from the cart.",
        responses={
            200: 'Product removed from cart successfully.',
            404: 'Product not found in cart.',
            400: 'Bad Request',
        }
    )
    def delete(self, request, cp_uid):
        try:
            if request.user.is_authenticated:
                cart = get_object_or_404(models.Cart, user=request.user)
                if cp_uid in cart.products:
                    cart.products.pop(cp_uid)
                    cart.total_price = sum(item['total_price'] for item in cart.products.values())
                    # Reset coupon info when removing a product
                    cart.applied_coupon = None
                    cart.coupon_discount_amount = Decimal('0.00')
                    cart.save()
                else:
                    return Response({"detail": "Product not found in cart."}, status=status.HTTP_404_NOT_FOUND)
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
                else:
                    return Response({"detail": "Product not found in cart."}, status=status.HTTP_404_NOT_FOUND)

            return Response({"detail": "Product removed successfully.", "cart": cart.products}, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return Response({"detail": error_message}, status=status.HTTP_400_BAD_REQUEST)       

class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]  # User must be authenticated to access this API
    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Process the checkout and merge session cart with user cart if available.",
        responses={
            200: 'Checkout processed successfully.',
            404: 'Cart not found for the user.',
            400: 'Bad Request',
        }
    )
    def get(self, request):
        try:
            user = request.user

            # Merge session cart with user cart if available
            session_cart = request.session.get('cart', {}).get('products', {})
            if session_cart:
                user_cart, created = models.Cart.objects.get_or_create(user=user)
                user_cart_products = user_cart.products or {}

                # Merge session cart products into user cart
                for key, value in session_cart.items():
                    if key in user_cart_products:
                        user_cart_products[key]['quantity'] += value['quantity']
                    else:
                        user_cart_products[key] = value

                # Calculate the total price and save the updated cart
                user_cart.products = user_cart_products
                user_cart.total_price = sum(
                    Decimal(item['product_discount_price']) * item['quantity']
                    for item in user_cart_products.values()
                )
                user_cart.save()

                # Clear session cart
                request.session.pop('cart', None)

            # Retrieve the user cart
            cart = models.Cart.objects.get(user=user)
            order_details = serializer.CartSerializer(cart).data

            # Extract necessary details for response
            final_cart_value = Decimal(order_details['products_data']['final_cart_value'])
            totaloriginalprice = Decimal(order_details['products_data']['gross_cart_value'])
            totalPrice = Decimal(order_details['products_data']['our_price'])
            Delivery = Decimal(order_details['products_data']['charges']['Delivery'])
            discount_price = totaloriginalprice - totalPrice
            addresses = user.address or []

            # Create Razorpay order
            razorpay_status, rz_order_id = create_order_in_razPay(
                amount=int(final_cart_value * 100)
            )

            # Prepare response data
            response_data = {
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

            return Response(response_data, status=status.HTTP_200_OK)

        except models.Cart.DoesNotExist:
            return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            error_message = f"An unexpected error occurred during checkout: {str(e)}"
            return Response({"detail": error_message}, status=status.HTTP_400_BAD_REQUEST)

class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]  # User must be authenticated to access this API

    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Process the checkout and merge session cart with user cart if available.",
        responses={
            200: 'Checkout processed successfully.',
            404: 'Cart not found for the user.',
            400: 'Bad Request',
        }
    )
    def get(self, request):
        try:
            user = request.user

            # Merge session cart with user cart if available
            session_cart = request.session.get('cart', {}).get('products', {})
            if session_cart:
                user_cart, created = models.Cart.objects.get_or_create(user=user)
                user_cart_products = user_cart.products or {}

                # Merge session cart into user cart
                for key, value in session_cart.items():
                    if key in user_cart_products:
                        user_cart_products[key]['quantity'] += value['quantity']
                    else:
                        user_cart_products[key] = value

                # Recalculate total price after merging
                user_cart.products = user_cart_products
                user_cart.total_price = sum(
                    Decimal(item['product_discount_price']) * item['quantity']
                    for item in user_cart_products.values()
                )
                user_cart.save()

                # Clear session cart
                request.session.pop('cart', None)

            # Retrieve user cart
            cart = models.Cart.objects.get(user=user)
            order_details = serializer.CartSerializer(cart).data
            print(f"Order Details : {order_details}")

            # Extract necessary details
            final_cart_value = Decimal(order_details['products_data']['final_cart_value'])
            totaloriginalprice = Decimal(order_details['products_data']['gross_cart_value'])
            totalPrice = Decimal(order_details['products_data']['our_price'])
            Delivery = Decimal(order_details['products_data']['charges']['Delivery'])
            discount_price = totaloriginalprice - totalPrice
            addresses = user.address or []

            # Create Razorpay order
            razorpay_status, rz_order_id = razorpay.create_order_in_razPay(
                amount=int(final_cart_value * 100)
            )

            # Prepare response data
            response_data = {
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
            return Response(response_data, status=status.HTTP_200_OK)

        except models.Cart.DoesNotExist:
            return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            error_message = f"An unexpected error occurred during checkout: {str(e)}"
            return Response({"detail": error_message}, status=status.HTTP_400_BAD_REQUEST)

    
class ApplyCouponAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can apply coupons

    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Apply a coupon to the user's cart and calculate the discounted price.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'coupon_code': openapi.Schema(type=openapi.TYPE_STRING, description='Coupon code to apply'),
            },
            required=['coupon_code'],
        ),
        responses={
            200: 'Coupon applied successfully.',
            400: 'Bad Request - No items in cart or invalid coupon.',
            404: 'Invalid coupon code or coupon not active.',
        }
    )
    def post(self, request):
        try:
            # Get the coupon code from the request data (JSON format)
            coupon_code = request.data.get('coupon_code')

            if not coupon_code:
                return Response({'success': False, 'message': 'Coupon code is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate if the coupon exists and is active
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)

                # Ensure the coupon is within its valid date range
                if coupon.valid_from <= timezone.now() <= coupon.valid_to:
                    # Get the user's cart
                    cart = models.Cart.objects.filter(user=request.user).first()

                    if cart and cart.total_price > 0:
                        # Apply the coupon to the cart
                        discount_price = self.calculate_coupon_discount(coupon, cart.total_price)
                        final_price = cart.total_price - float(discount_price)

                        # Update the cart with the applied coupon and discount
                        cart.applied_coupon = coupon
                        cart.total_price = float(round(final_price, 2))
                        cart.coupon_discount_amount = discount_price
                        cart.save()

                        return Response({
                            'success': True, 
                            'final_price': float(final_price),
                            'discount_price': float(discount_price),
                            'message': 'Coupon applied successfully!'
                        }, status=status.HTTP_200_OK)

                    else:
                        return Response({'success': False, 'message': 'No items in the cart.'}, status=status.HTTP_400_BAD_REQUEST)

                else:
                    return Response({'success': False, 'message': 'Coupon is expired or not valid right now.'}, status=status.HTTP_400_BAD_REQUEST)

            except Coupon.DoesNotExist:
                return Response({'success': False, 'message': 'Invalid coupon code.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'success': False, 'message': f'Something went wrong: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def calculate_coupon_discount(self, coupon, total_price):
        """
        Calculate the discount based on the coupon type.
        """
        discount_price = Decimal('0.00')

        if coupon.discount_type == 'fixed':
            discount_price = Decimal(coupon.discount_value)
        elif coupon.discount_type == 'percent':
            discount_price = Decimal(total_price) * (Decimal(coupon.discount_value) / Decimal('100'))
        
        return discount_price
    
class RemoveCouponAPIView(APIView):
    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Remove an applied coupon from the user's cart and recalculate the total price.",
        responses={
            200: 'Coupon removed successfully.',
            400: 'Bad Request - No coupon applied to remove.',
            404: 'Cart not found for the user.',
        }
    )
    def post(self, request):
        if request.user.is_authenticated:
            cart = models.Cart.objects.filter(user=request.user).first()
            if cart and cart.applied_coupon:
                # Recalculate the total price by adding the discount amount back
                cart.total_price = float(round(cart.total_price + float(cart.coupon_discount_amount), 2))
                cart.applied_coupon = None  # Remove the coupon
                cart.coupon_discount_amount = 0
                cart.save()

                return Response({"message": "Coupon removed successfully.", "total_price": cart.total_price}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No coupon applied to remove."}, status=status.HTTP_400_BAD_REQUEST)

        else:
            # For non-authenticated users, handle coupon removal via session
            if 'applied_coupon' in request.session:
                final_cart_value = Decimal(request.session.get('total_price', '0.00'))
                discount_amount = Decimal(request.session.get('coupon_discount_amount', '0.00'))

                # Recalculate the session cart's total price by adding the discount back
                request.session['total_price'] = float(round(final_cart_value + discount_amount, 2))
                request.session['coupon_discount_amount'] = float(0.00)
                request.session.modified = True
                del request.session['applied_coupon']  # Remove the applied coupon from session

                return Response({"message": "Coupon removed successfully.", "total_price": request.session['total_price']}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No coupon applied to remove."}, status=status.HTTP_400_BAD_REQUEST)