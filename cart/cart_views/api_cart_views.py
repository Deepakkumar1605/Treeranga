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

from product.models import SimpleProduct


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
        try:
            if request.user.is_authenticated:
                cart, _ = models.Cart.objects.get_or_create(user=request.user)
                is_user_authenticated = True
            else:
                cart = request.session.get('cart', {'products': {}})
                is_user_authenticated = False

            # Try to get the SimpleProduct object
            product_obj = get_object_or_404(SimpleProduct, id=product_id)

            # Rest of the logic
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
                products[product_key]['quantity'] += 1
                products[product_key]['total_price'] += product_obj.product_discount_price
            else:
                products[product_key] = {
                    'info': product_info,
                    'quantity': 1,
                    'total_price': product_obj.product_discount_price
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

            return Response({"message": f"{product_obj.product.name} added to cart."}, status=status.HTTP_200_OK)
        
        except Http404:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            print(f"Add to cart error: {e}")
            return Response({"error": f"An error occurred: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)