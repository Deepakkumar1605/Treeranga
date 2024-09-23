from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from helpers import swagger_documentation
from orders.models import Order
from orders.serializer import OrderSerializer
from product.models import Products

class UserOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    @swagger_auto_schema(
        tags=["Order"],
        operation_description="Show user orders. Requires authentication.",
        responses={
            200: 'Successfully retrieved user orders.',
            401: 'Unauthorized - Authentication required.',
            404: 'Orders not found for this user.'
        }
    )
    def get(self, request):
        user = request.user  # Get the logged-in user
        
        orders = Order.objects.filter(user=user).order_by("-id")  # Fetch orders for the user
        if orders.exists():
            serializer = OrderSerializer(orders, many=True)  # Serialize the data
            return Response(serializer.data, status=200)  # Return serialized data as JSON response
        else:
            return Response({"detail": "No orders found for this user."}, status=404)

class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Order"],
        operation_description="Get details of a specific order by its unique identifier.",
        manual_parameters=swagger_documentation.orderlist_post,
        responses={
            200: 'Order details retrieved successfully.',
            404: 'Order or Product not found.',
            401: 'Unauthorized access.'
        }
    )
    def get(self, request, order_uid):
        order = get_object_or_404(Order, uid=order_uid)

        product_list = []
        product_quantity = []
        total_quantity = 0
        grand_total = 0.0
        total_cgst = 0.0
        total_sgst = 0.0

        # Extract values from the order's metadata
        order_meta_data = order.order_meta_data
        grand_total = float(order_meta_data.get('final_cart_value', '0.00'))
        discount_amount = float(order_meta_data.get('discount_amount', '0.00'))
        gross_cart_value = float(order_meta_data.get('gross_cart_value', '0.00'))
        total_cart_items = int(order_meta_data.get('total_cart_items', 0))
        delivery_charge = float(order_meta_data.get('charges', {}).get('Delivery', '0.00'))

        products = []
        quantities = []
        price_per_unit = []
        total_prices = []

        # Calculate total CGST and SGST
        for product_id, details in order_meta_data.get('products', {}).items():
            total_cgst += float(details.get('cgst_amount', '0.00'))
            total_sgst += float(details.get('sgst_amount', '0.00'))
            
            # Fetch product and calculate price details
            product = get_object_or_404(Products, id=details['id'])
            products.append(product)
            quantities.append(details['quantity'])
            price_per_unit.append(details['product_discount_price'])
            total_prices.append(float(details['total_discounted_price']))
            total_quantity += int(details['quantity'])

        # Bundle product info into a list of dictionaries
        product_info = [
            {
                'product': {
                    'name': product.name,
                    'id': product.id,
                    'price_per_unit': price_per_unit[idx],
                    'total_price': total_prices[idx]
                },
                'quantity': quantities[idx]
            }
            for idx, product in enumerate(products)
        ]

        response_data = {
            'order': {
                'id': order.id,
                'uid': order.uid,
                'payment_method': order.payment_method,
            },
            'order_details': {
                'grand_total': grand_total,
                'total_quantity': total_quantity,
                'discount_amount': discount_amount,
                'gross_cart_value': gross_cart_value,
                'total_cart_items': total_cart_items,
                'cgst_amount': total_cgst,
                'sgst_amount': total_sgst,
                'delivery_charge': delivery_charge,
            },
            'products': product_info,
            'MEDIA_URL': settings.MEDIA_URL
        }

        return Response(response_data, status=200)