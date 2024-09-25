from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from helpers import utils
from product import models
from rest_framework import status
from product.serializers import CategorySerializer, ImageGallerySerializer, ProductsSerializer, ProductsSerializer, SimpleProductSerializer, VariantImageGallerySerializer, VariantProductSerializer
from drf_yasg import openapi
from rest_framework.views import APIView

from product_variations.models import VariantImageGallery, VariantProduct
from wishlist.models import WishList
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class AddToWishlistAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_description="Add a product to wishlist",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the product'),
                'is_variant': openapi.Schema(type=openapi.TYPE_STRING, description='Is the product a variant (yes/no)'),
            }
        ),
        responses={
            200: 'Product successfully added to wishlist',
            400: 'Bad Request - Invalid data provided',
            401: 'Unauthorized - User is not authenticated',
        }
    )
    def post(self, request):
        try:
            data = request.data
            product_id = data.get('product_id')
            is_variant = data.get('is_variant')

            if not product_id:
                return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            if is_variant == "yes":
                product = get_object_or_404(VariantProduct, id=product_id)
            else:
                product = get_object_or_404(models.SimpleProduct, id=product_id)

            wishlist, created = WishList.objects.get_or_create(user=request.user)

            products = wishlist.products.get('items', [])

            if not any(str(item['id']) == str(product_id) and item['is_variant'] == is_variant for item in products):
                products.append({
                    'id': product_id,
                    'is_variant': is_variant,
                    'product_name': product.product.name  # Adjust according to your model
                })
                wishlist.products['items'] = products
                wishlist.save()

            return Response({"message": "Product added to wishlist"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class RemoveFromWishlistAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view

    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_description="Remove a product from wishlist",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the product'),
            }
        ),
        responses={
            200: 'Product successfully removed from wishlist',
            400: 'Bad Request - Invalid data provided',
            401: 'Unauthorized - User is not authenticated',
        }
    )
    def post(self, request):
        try:
            data = request.data
            product_id = data.get('product_id')

            if not product_id:
                return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            wishlist = get_object_or_404(WishList, user=request.user)

            products = wishlist.products.get('items', [])
            wishlist.products['items'] = [item for item in products if str(item['id']) != str(product_id)]
            wishlist.save()

            return Response({"message": "Product removed from wishlist"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class AllWishlistItemsAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view

    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_description="Retrieve all items in the user's wishlist",
        responses={
            200: 'Successfully retrieved wishlist items',
            401: 'Unauthorized - User is not authenticated',
        }
    )
    def get(self, request):
        wishlist, created = WishList.objects.get_or_create(user=request.user)
        product_items = wishlist.products.get('items', [])
        detailed_products = []

        for item in product_items:
            product_id = item['id']
            is_variant = item['is_variant']
            product_name = item['product_name']

            if is_variant == "yes":
                product = get_object_or_404(VariantProduct, id=product_id)
                product_price = product.product_discount_price
                product_max_price = product.product_max_price
                product_image = product.product.image.url
            else:
                simple_product = get_object_or_404(models.SimpleProduct, id=product_id)
                product_price = simple_product.product_discount_price
                product_max_price = simple_product.product_max_price
                product_image = simple_product.product.image.url if simple_product.product.image else None

            detailed_products.append({
                'id': product_id,
                'name': product_name,
                'price': product_price,
                'max_price': product_max_price,
                'image': product_image,
                'is_variant': is_variant
            })

        return Response({"wishlist_items": detailed_products}, status=status.HTTP_200_OK)

