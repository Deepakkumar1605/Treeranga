from decimal import Decimal
import json
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
from django.core.exceptions import ValidationError
from cart.models import Cart

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from helpers import swagger_documentation
from orders.models import Order
from orders.serializer import OrderSerializer
from product.forms import ProductReviewForm
from product.models import ProductReview, Products
from product_variations.models import VariantProduct
from rest_framework import status
from rest_framework.exceptions import NotFound
from payment.payment_views.delhivery_api import track_delhivery_order

class UserOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Order"],
        manual_parameters=swagger_documentation.user_order_get_params,
        operation_description="Retrieve all orders associated with the authenticated user.",
        responses={
            200: "Successfully retrieved user orders.",
            401: 'Unauthorized - Authentication required.',
            404: 'No orders found for this user.'
        }
    )
    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user).order_by("-id")
        detailed_orders = []

        for order in orders:
            products_info = order.products
            order_meta_data = order.order_meta_data

            order_details = {
                'order_uid': order.uid,
                'order_status': order.order_status,
                'payment_status': order.payment_status,
                'date': order.date,
                'total_cart_value': order_meta_data.get("final_cart_value"),
                'products': []
            }

            for product_key, product_data in products_info.items():
                product_details = product_data['info']
                quantity = product_data['quantity']
                total_price = product_data['total_price']

                product_entry = {
                    'name': product_details.get('name'),
                    'image': product_details.get('image'),
                    'slug': product_details.get('slug'),
                    'product_id': product_details.get('product_id'),
                    'quantity': quantity,
                    'price_per_unit': product_details.get('discount_price'),
                    'total_price': total_price
                }
                order_details['products'].append(product_entry)

            detailed_orders.append(order_details)

        if detailed_orders:
            return Response({'orders': detailed_orders}, status=200)
        else:
            return Response({"detail": "No orders found for this user."}, status=404)


class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Order"],
        manual_parameters=swagger_documentation.order_detail_params,
        operation_description="Retrieve specific product details within an order for the authenticated user.",
        responses={
            200: "Successfully retrieved product details within the order.",
            404: "Order or product not found."
        }
    )
    def get(self, request, order_uid):
        try:
            # Retrieve the order and its metadata
            order = get_object_or_404(Order, uid=order_uid)
            ref_id = str(order.uid)
            
            # Get tracking data
            tracking_response = track_delhivery_order(ref_id=ref_id)
            tracking_data = tracking_response.get('data', []) if tracking_response.get('success') else []

            # Initialize variables for order details
            grand_total = float(order.order_meta_data.get('final_cart_value', '0.00'))
            discount_amount = float(order.order_meta_data.get('discount_amount', '0.00'))
            gross_cart_value = float(order.order_meta_data.get('gross_cart_value', '0.00'))
            total_cart_items = int(order.order_meta_data.get('total_cart_items', 0))
            delivery_charge = float(order.order_meta_data.get('charges', {}).get('Delivery', '0.00'))
            applied_coupon = order.order_meta_data.get('applied_coupon', None)
            coupon_discount_amount = order.order_meta_data.get('coupon_discount_amount', '0.00')
            total_cgst = 0.0
            total_sgst = 0.0
            total_quantity = 0

            # Gather products, quantities, and price details
            products_data = []
            for product_id, details in order.order_meta_data.get('products', {}).items():
                product = get_object_or_404(Products, id=details['id'])
                product_info = {
                    'id': product.id,
                    'name': product.name,
                    'quantity': details['quantity'],
                    'price_per_unit': details['price_per_unit'],
                    'total_price': float(details['total_discounted_price']),
                }
                products_data.append(product_info)
                total_cgst += float(details.get('cgst_amount', '0.00'))
                total_sgst += float(details.get('sgst_amount', '0.00'))
                total_quantity += int(details['quantity'])

            # Construct response data
            response_data = {
                'order_id': order.id,
                'order_uid': order.uid,
                'grand_total': grand_total,
                'discount_amount': discount_amount,
                'gross_cart_value': gross_cart_value,
                'total_cart_items': total_cart_items,
                'delivery_charge': delivery_charge,
                'applied_coupon': applied_coupon,
                'coupon_discount_amount': coupon_discount_amount,
                'cgst_amount': total_cgst,
                'sgst_amount': total_sgst,
                'total_quantity': total_quantity,
                'payment_method': order.payment_method,
                'products': products_data,
                'tracking_data': tracking_data,
                'media_url': settings.MEDIA_URL,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)





class SubmitReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Review"],
        manual_parameters=swagger_documentation.review_post_params,
        operation_description="Submit a review for a product or product variant.",
        responses={
            201: "Review successfully submitted.",
            400: "Invalid form data or missing product/variant.",
            404: "Product or variant not found."
        }
    )
    def post(self, request):
        # Validate and process data from the request
        form = ProductReviewForm(request.data)
        if form.is_valid():
            product_slug = request.query_params.get('product_slug')
            variant_slug = request.query_params.get('variant_slug', None)  # Optional for variant products

            # Get the main product or variant
            product = get_object_or_404(Products, slug=product_slug)
            variant_product = get_object_or_404(VariantProduct, slug=variant_slug) if variant_slug else None

            # Retrieve rating and review text from validated form data
            rating = form.cleaned_data['rating']
            review_text = form.cleaned_data['review']

            # Create and save the review
            review = ProductReview.objects.create(
                product=None if variant_product else product,  # Use main product if not a variant
                variant_product=variant_product,
                user=request.user,
                rating=rating,
                review=review_text,
            )
            review.save()

            return Response({"detail": "Review successfully submitted."}, status=status.HTTP_201_CREATED)

        # Handle invalid form
        return Response({"error": "There was a problem with your review submission."}, status=status.HTTP_400_BAD_REQUEST)




class SubmitReviewPageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Review"],
        operation_description="Retrieve data required to submit a review for a product, including product information and a 5-star rating range.",
        responses={
            200: "Successfully retrieved review page data.",
            404: "Product not found.",
            400: "An unexpected error occurred."
        }
    )
    def get(self, request, slug):
        try:
            # Retrieve the product using the provided slug
            product = get_object_or_404(Products, slug=slug)
            
            # Define the range for star ratings (1 to 5 for a 5-star system)
            star_range = list(range(1, 6))

            # Create a response with product data and the star range
            response_data = {
                "product": {
                    "name": product.name,
                    "slug": product.slug,
                    "description": product.description,
                    "price": product.price,
                    # Add other fields as required
                },
                "star_range": star_range
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import status

class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=["Order"],
        operation_description="Order create API",
        responses={
            200: 'Successfully retrieved user orders.',
            401: 'Unauthorized - Authentication required.',
            404: 'Orders not found for this user.'
        }
    )
    def post(self, request):
        try:
            # Extract data from the request
            address_id = request.data.get("address_id")  # ID can be used to choose an address if there are multiple
            transaction_id = request.data.get("transaction_id")
            signature = request.data.get("signature")
            token = request.data.get("token")

            # Validate required fields
            if not all([transaction_id, signature, token]):
                return Response(
                    {"error": "Missing required fields."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the user and verify the token
            user = request.user
            if user.token != token:
                return Response(
                    {"error": "Invalid token."},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Check if the user has requested deletion
            if user.deletion_requested:
                return Response(
                    {"error": "Account deletion requested. Order cannot be placed."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Retrieve the address from JSONField
            address = user.address.get(address_id) if user.address else None
            if not address:
                return Response(
                    {"error": "Address not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get the user's cart
            cart = Cart.objects.filter(user=user).first()
            if not cart or not cart.products:
                return Response(
                    {"error": "Cart is empty."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create Order
            order = Order.objects.create(
                user=user,
                address=json.dumps(address),  # Store address as JSON
                transaction_id=transaction_id,
                signature=signature,
                total_amount=cart.total_price,
                status="Pending"
            )

            # Transfer cart items to order
            order_products = []
            for product_key, product_info in cart.products.items():
                order_products.append({
                    "product_id": product_info["product_id"],
                    "quantity": product_info["quantity"],
                    "price": Decimal(product_info["total_price"])
                })
            order.products = json.dumps(order_products)  # Store products in JSON format
            order.save()

            # Clear the cart after order is created
            cart.products = {}
            cart.total_price = Decimal("0.00")
            cart.save()

            # Serialize the created order
            serializer = OrderSerializer(order)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)