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

from payment.razorpay import create_order_in_razPay
from product.models import SimpleProduct
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

        # Fetch cart items based on user authentication
        if user.is_authenticated:
            cart = models.Cart.objects.filter(user=user).first()
            if not cart or not cart.products:
                products = {}
            else:
                products = cart.products or {}
        else:
            cart = None
            products = request.session.get('cart', {}).get('products', {})

        # Calculate the cart details
        totaloriginalprice = Decimal('0.00')
        totalPrice = Decimal('0.00')
        GST = Decimal('0.00')
        Delivery = Decimal('0.00')
        final_cart_value = Decimal('0.00')

        for product_key, product_info in products.items():
            max_price = Decimal(product_info['info'].get('max_price', '0.00'))
            discount_price = Decimal(product_info['info'].get('discount_price', '0.00'))
            quantity = product_info.get('quantity', 0)
            
            totaloriginalprice += max_price * quantity
            totalPrice += discount_price * quantity

        if totalPrice > 0:
            discount_price = totaloriginalprice - totalPrice
            GST = totalPrice * Decimal(settings.GST_CHARGE)
            final_cart_value = totalPrice + GST

            if final_cart_value < Decimal(settings.DELIVARY_FREE_ORDER_AMOUNT):
                Delivery = Decimal(settings.DELIVARY_CHARGE_PER_BAG)

            final_cart_value += Delivery
        else:
            discount_price = Decimal('0.00')

        if user.is_authenticated and cart:
            cart.total_price = float(totalPrice)
            cart.save()

        # Prepare the serialized data
        cart_data = serializer.CartSerializer(cart).data if cart else {}

        response_data = {
            'products': products,
            'totaloriginalprice': float(totaloriginalprice),
            'totalPrice': float(totalPrice),
            'GST': float(GST),
            'Delivery': float(Delivery),
            'final_cart_value': float(final_cart_value),
            'discount_price': float(discount_price),
            **cart_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)
    

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
    permission_classes = [IsAuthenticated]  # Ensuring the user is authenticated for this view

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
        operation_type = request.query_params.get('operation')

        try:
            cart = models.Cart.objects.get(user=request.user)
            products = cart.products or {}
        except models.Cart.DoesNotExist:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

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
                            {"error": f"Cannot add more than {max_quantity} of this product."},
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
            return Response({"error": f"Product with UID {c_p_uid} not found in cart."}, status=status.HTTP_404_NOT_FOUND)

        # Update the cart and save changes
        cart.products = products
        cart.total_price = sum(item['total_price'] for item in products.values())
        cart.save()

        return Response({"message": "Cart updated successfully.", "cart": products}, status=status.HTTP_200_OK)
    
class RemoveFromCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
                    cart.save()
                    return Response({"success": "Product removed from cart successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Product not found in cart."}, status=status.HTTP_404_NOT_FOUND)
            else:
                cart = request.session.get('cart', {'products': {}})
                products = cart.get('products', {})
                if cp_uid in products:
                    products.pop(cp_uid)
                    cart['total_price'] = sum(item['total_price'] for item in products.values())
                    cart['products'] = products
                    request.session['cart'] = cart
                    request.session.modified = True
                    return Response({"success": "Product removed from cart successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Product not found in cart."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Error while removing product from cart: {e}")
            return Response({"error": "An error occurred while removing the product from the cart."}, status=status.HTTP_400_BAD_REQUEST)
        

class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
        user = request.user
        try:
            # Merge session cart with user cart if available
            session_cart = request.session.get('cart', {}).get('products', {})
            if session_cart:
                user_cart, created = models.Cart.objects.get_or_create(user=user)
                user_cart_products = user_cart.products or {}

                for key, value in session_cart.items():
                    if key in user_cart_products:
                        user_cart_products[key]['quantity'] += value['quantity']
                    else:
                        user_cart_products[key] = value

                # Update total price
                user_cart.products = user_cart_products
                user_cart.total_price = sum(
                    Decimal(item['product_discount_price']) * item['quantity'] 
                    for item in user_cart_products.values()
                )
                user_cart.save()

                # Clear session cart
                request.session.pop('cart', None)

            # Fetch user cart
            cart = get_object_or_404(models.Cart, user=user)
        except models.Cart.DoesNotExist:
            return Response({"error": "Cart does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error in checkout process: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize cart details
        cart_data = serializer.CartSerializer(cart).data

        # Extract necessary details from serialized data
        final_cart_value = Decimal(cart_data['products_data']['final_cart_value'])
        totaloriginalprice = Decimal(cart_data['products_data']['gross_cart_value'])
        totalPrice = Decimal(cart_data['products_data']['our_price'])
        Delivery = Decimal(cart_data['products_data']['charges']['Delivery'])
        discount_price = totaloriginalprice - totalPrice
        addresses = user.address or []  # Assuming you have an address field on the user model

        # Razorpay order creation
        status, rz_order_id = create_order_in_razPay(
            amount=int(final_cart_value * 100)  # Amount in paise
        )

        if not status:
            return Response({"error": "Failed to create Razorpay order."}, status=status.HTTP_400_BAD_REQUEST)

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
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
