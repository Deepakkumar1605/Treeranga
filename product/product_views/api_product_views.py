from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from product import models
from rest_framework import status
from product.serializers import CategorySerializer, ProductSerializer, ProductsSerializer, SimpleProductSerializer, VariantProductSerializer

from rest_framework.views import APIView

from product_variations.models import VariantProduct

class CategoryListAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view

    @swagger_auto_schema(
        tags=["Product"],
        operation_description="All categories",
        responses={
            200: 'Successfully retrieved the categories',
            401: 'Unauthorized'
        }
    )
    def get(self, request):
        categories = models.Category.objects.all()  # Retrieve all categories
        category_serializer = CategorySerializer(categories, many=True)  # Serialize the categories

        return Response({'categories': category_serializer.data})  # Return serialized data

class ShowProductsAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view

    @swagger_auto_schema(
        tags=["Product"],
        operation_description="Product List",
        responses={
            200: 'Successfully retrieved the products',
            401: 'Unauthorized',
            404: 'Category not found'
        }
    )
    def get(self, request, category_name):
        category_obj = get_object_or_404(models.Category, title=category_name)

        products_for_this_category = models.Products.objects.filter(category=category_obj)
        
        product_serializer = ProductSerializer(products_for_this_category, many=True)

        return Response({
            'category': category_obj.title,
            'products': product_serializer.data
        })
    
class ProductDetailsApiView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="Product details",
        responses={
            200: 'Successfully retrieved the products',
            401: 'Unauthorized',
            404: 'Category not found'
        }
    )
    def get(self, request, p_id):
        user = request.user
        product_obj = get_object_or_404(models.Products, id=p_id)

        # Get the first SimpleProduct for the current product
        simple_product = models.SimpleProduct.objects.filter(product=product_obj).first()
        image_gallery = None
        if simple_product:
            image_gallery = models.ImageGallery.objects.filter(simple_product=simple_product).first()

        similar_product_list = models.Products.objects.filter(category=product_obj.category).exclude(id=product_obj.id)[:5]

        # Fetch the SimpleProduct instances for similar products
        similar_simple_products = []
        for product in similar_product_list:
            simple_product = models.SimpleProduct.objects.filter(product=product).first()
            if simple_product:
                similar_simple_products.append({
                    'product': ProductSerializer(product).data,
                    'simple_product': SimpleProductSerializer(simple_product).data
                })


        data = {
            'product': ProductSerializer(product_obj).data,
            'simple_product': SimpleProductSerializer(simple_product).data if simple_product else None,
            'similar_simple_products': similar_simple_products,
        }

        return Response(data)
    
class AllTrendingProductsAPIView(APIView):
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="All Trending Product",
        responses={
            200: 'Successfully retrieved the trending product',
            401: 'Unauthorized'
        }
    )
    def get(self, request):
        trending_products = models.Products.objects.filter(trending="yes")
        serializer = ProductSerializer(trending_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AllNewProductsAPIView(APIView):
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="All New Product",
        responses={
            200: 'Successfully retrieved the new product',
            401: 'Unauthorized'
        }
    )
    def get(self, request):
        new_products = models.Products.objects.filter(show_as_new="yes")
        serializer = ProductSerializer(new_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ShowProductsAPIView(APIView):
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="Show all Product",
        responses={
            200: 'Successfully retrieved the all product',
            401: 'Unauthorized'
        }
    )
    def get(self, request, category_name):
        category_obj = get_object_or_404(models.Category, title=category_name)
        products_for_this_category = models.Products.objects.filter(category=category_obj)

        products_with_variants = []
        
        for product in products_for_this_category:
            if product.product_type == "simple":
                simple_products = models.SimpleProduct.objects.filter(product=product, is_visible=True)
                products_with_variants.append({
                    'product': ProductsSerializer(product).data,
                    'simple_products': SimpleProductSerializer(simple_products, many=True).data,
                    'variant': "no",
                })
            elif product.product_type == "variant":
                variant_products = VariantProduct.objects.filter(product=product, is_visible=True)
                products_with_variants.append({
                    'product': ProductsSerializer(product).data,
                    'variant_products': VariantProductSerializer(variant_products, many=True).data,
                    'variant': "yes",
                })

        return Response({
            'products_with_variants': products_with_variants,
            'category': CategorySerializer(category_obj).data,
            "MEDIA_URL": settings.MEDIA_URL,
        }, status=status.HTTP_200_OK)
