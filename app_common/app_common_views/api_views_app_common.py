from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from helpers import api_permission
from product.models import Category, Products
from product.serializers import CategorySerializer, ProductSerializer
from rest_framework import status


class HomeAPIView(APIView):
    
    @swagger_auto_schema(
        tags=["Home"],
        operation_description="Retrieve home page data including categories, trending products, and new products.",
        responses={
            200: 'Successful response with categories, trending products, and new products',
            404: 'Not found',
            500: 'Internal server error',
        }
    )
    def get(self, request):
        if request.user.is_superuser:
            return Response({"detail": "Redirecting to admin dashboard"}, status=status.HTTP_302_FOUND)

        # Get all categories
        categories = Category.objects.all()
        category_serializer = CategorySerializer(categories, many=True)

        # Handle Trending Products
        trending_products = Products.objects.filter(trending="yes").order_by('-id')[:7]
        trending_product_serializer = ProductSerializer(trending_products, many=True)

        # Handle New Products
        new_products = Products.objects.filter(show_as_new="yes").order_by('-id')[:7]
        new_product_serializer = ProductSerializer(new_products, many=True)

        context = {
            'categories': category_serializer.data,
            'trending_products': trending_product_serializer.data,
            'new_products': new_product_serializer.data,
            'MEDIA_URL': settings.MEDIA_URL,
        }

        return Response(context, status=status.HTTP_200_OK)
    