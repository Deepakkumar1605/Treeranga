from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from helpers import swagger_documentation
from product import models
from rest_framework import status
from product.serializers import CategorySerializer, ImageGallerySerializer, ProductSerializer, ProductsSerializer, SimpleProductSerializer, VariantImageGallerySerializer, VariantProductSerializer
from django.db.models import Q
from rest_framework.views import APIView

from product_variations.models import VariantImageGallery, VariantProduct

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


class ProductDetailsAPIView(APIView):
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="Product Details",
        responses={
            200: 'Successfully retrieved the product Details',
            401: 'Unauthorized'
        }
    )
    def get(self, request, p_id):
        user = request.user
        variant_param = request.GET.get('variant', '')
        
        # Fetch product object based on variant
        if variant_param == "yes":
            product_obj = get_object_or_404(VariantProduct, id=p_id)
        elif variant_param == "no":
            product_obj = get_object_or_404(models.SimpleProduct, id=p_id)
        else:
            return Response({"error": "No variant selected"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Serialize category data
        category_obj = models.Category.objects.all()
        category_data = CategorySerializer(category_obj, many=True).data

        all_variants_of_this = []
        attributes = {}
        active_variant_attributes = {}
        product_images = []
        product_videos = []

        # Handle product images and variants
        if product_obj:
            if product_obj.product.product_type == "simple":
                image_gallery = models.ImageGallery.objects.filter(simple_product=product_obj).first()
                if image_gallery:
                    product_images = ImageGallerySerializer(image_gallery).data['images']
                    product_videos = ImageGallerySerializer(image_gallery).data['video']
            elif product_obj.product.product_type == "variant":
                image_gallery = VariantImageGallery.objects.filter(variant_product=product_obj).first()
                if image_gallery:
                    product_images = VariantImageGallerySerializer(image_gallery).data['images']
                    product_videos = VariantImageGallerySerializer(image_gallery).data['video']
                
                avp = VariantProduct.objects.filter(product=product_obj.product)
                for av in avp:
                    variant_image_gallery = VariantImageGallery.objects.filter(variant_product=av).first()
                    variant_images = VariantImageGallerySerializer(variant_image_gallery).data['images'] if variant_image_gallery else []
                    variant_videos = VariantImageGallerySerializer(variant_image_gallery).data['video'] if variant_image_gallery else []

                    all_variants_of_this.append({
                        'product': VariantProductSerializer(av).data,
                        'variant': "yes",
                        'images': variant_images,
                        'videos': variant_videos
                    })

                for variant in avp:
                    variant_combination = variant.variant_combination
                    for attribute, value in variant_combination.items():
                        if attribute not in attributes:
                            attributes[attribute] = set()
                        attributes[attribute].add(value)

                active_variant_attributes = {attr: val for attr, val in product_obj.variant_combination.items()}
        
        attributes = {attribute: sorted(values) for attribute, values in attributes.items()}

        # Similar products
        product_list_category_wise = models.Products.objects.filter(category=product_obj.product.category)
        all_simple_and_variant_similar = []

        for product in product_list_category_wise:
            if product.product_type == "simple":
                simple_products = models.SimpleProduct.objects.filter(product=product, is_visible=True).exclude(id=product_obj.id)
                for sp in simple_products:
                    gallery = models.ImageGallery.objects.filter(simple_product=sp).first()
                    all_simple_and_variant_similar.append({
                        'product': SimpleProductSerializer(sp).data,
                        'variant': "no",
                        'images': ImageGallerySerializer(gallery).data['images'] if gallery else [],
                        'videos': ImageGallerySerializer(gallery).data['video'] if gallery else []
                    })
            elif product.product_type == "variant":
                variant_product = VariantProduct.objects.filter(product=product, is_visible=True).exclude(id=product_obj.id).first()
                if variant_product:
                    gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                    all_simple_and_variant_similar.append({
                        'product': VariantProductSerializer(variant_product).data,
                        'variant': "yes",
                        'images': VariantImageGallerySerializer(gallery).data['images'] if gallery else [],
                        'videos': VariantImageGallerySerializer(gallery).data['video'] if gallery else []
                    })

        # Return JSON response
        return Response({
            'user': user.id if user.is_authenticated else None,
            'category': category_data,
            'product': VariantProductSerializer(product_obj).data if variant_param == "yes" else SimpleProductSerializer(product_obj).data,
            'all_variants_of_this': all_variants_of_this,
            'images': product_images,
            'videos': product_videos,
            'similar_products': all_simple_and_variant_similar,
            'attributes': attributes,
            'active_variant_attributes': active_variant_attributes,
        }, status=status.HTTP_200_OK)
    
class AllTrendingProductsAPIView(APIView):
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="All New Product",
        responses={
            200: 'Successfully retrieved the new product',
            401: 'Unauthorized'
        }
    )
    def get(self, request):
        trending_products = models.Products.objects.filter(trending="yes")
        updated_trending_products = []

        for product in trending_products:
            # Check for simple products
            if product.product_type == "simple":
                simple_products = models.SimpleProduct.objects.filter(product=product, is_visible=True)
                for simple_product in simple_products:
                    image_gallery = models.ImageGallery.objects.filter(simple_product=simple_product).first()
                    images = image_gallery.images if image_gallery else []
                    videos = image_gallery.video if image_gallery else []
                    updated_trending_products.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'product_type': "simple",
                        'simple_product': SimpleProductSerializer(simple_product).data,
                        'variant': "no",
                        'images': images,
                        'videos': videos
                    })
            # Check for variant products
            elif product.product_type == "variant":
                variant_products = VariantProduct.objects.filter(product=product, is_visible=True)
                for variant_product in variant_products:
                    variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                    images = variant_image_gallery.images if variant_image_gallery else []
                    videos = variant_image_gallery.video if variant_image_gallery else []
                    updated_trending_products.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'product_type': "variant",
                        'variant_product': VariantProductSerializer(variant_product).data,
                        'variant': "yes",
                        'images': images,
                        'videos': videos
                    })

        return Response({
            'trending_products': updated_trending_products
        }, status=status.HTTP_200_OK)
    
class AllNewProductsAPIView(APIView):
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="All Trending Product",
        responses={
            200: 'Successfully retrieved the trending product',
            401: 'Unauthorized'
        }
    )
    def get(self, request):
        new_products = models.Products.objects.filter(show_as_new="yes")
        updated_new_products = []

        for product in new_products:
            # Check for simple products
            if product.product_type == "simple":
                simple_products = models.SimpleProduct.objects.filter(product=product, is_visible=True)
                for simple_product in simple_products:
                    image_gallery = models.ImageGallery.objects.filter(simple_product=simple_product).first()
                    images = image_gallery.images if image_gallery else []
                    videos = image_gallery.video if image_gallery else []
                    updated_new_products.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'product_type': "simple",
                        'simple_product': SimpleProductSerializer(simple_product).data,
                        'variant': "no",
                        'images': images,
                        'videos': videos
                    })
            # Check for variant products
            elif product.product_type == "variant":
                variant_products = VariantProduct.objects.filter(product=product, is_visible=True)
                for variant_product in variant_products:
                    variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                    images = variant_image_gallery.images if variant_image_gallery else []
                    videos = variant_image_gallery.video if variant_image_gallery else []
                    updated_new_products.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'product_type': "variant",
                        'variant_product': VariantProductSerializer(variant_product).data,
                        'variant': "yes",
                        'images': images,
                        'videos': videos
                    })

        return Response({
            'new_products': updated_new_products
        }, status=status.HTTP_200_OK)
    

class SearchProductNamesAPIView(APIView):
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="Search Product Names",
        manual_parameters=[swagger_documentation.search_term_param],  # Add search_term as a body parameter
        responses={
            200: 'Successfully retrieved Search Product Names',
            401: 'Unauthorized'
        }
    )
    def post(self, request, *args, **kwargs):
        search_term = request.data.get('search_term', '').strip()  # Read from request body
        if search_term:
            products = models.Products.objects.filter(name__icontains=search_term).distinct('name')
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)
class SearchItemsAPIView(APIView):
    
    serializer_class = ProductSerializer
    @swagger_auto_schema(
        tags=["Product"],
        operation_description="Search Items",
        responses={
            200: 'Successfully retrieved Search Items',
            401: 'Unauthorized'
        }
    )
    def get(self, request, *args, **kwargs):
        search_title = request.GET.get("search_title", "").strip()
        if not search_title:
            return Response({"error": "Search title is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initial product query based on the search title
        products = models.Products.objects.filter(name__icontains=search_title)

        # Get filter criteria from request
        category_id = request.GET.get('category')
        product_type = request.GET.get('product_type')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        in_stock = request.GET.get('in_stock')

        # Apply additional filters if provided
        if category_id:
            products = products.filter(category_id=category_id)

        # Filter by price range
        if min_price and max_price:
            simple_product_ids = models.SimpleProduct.objects.filter(
                product_discount_price__gte=min_price, 
                product_discount_price__lte=max_price
            ).values_list('product_id', flat=True)

            variant_product_ids = VariantProduct.objects.filter(
                product_discount_price__gte=min_price, 
                product_discount_price__lte=max_price
            ).values_list('product_id', flat=True)

            products = products.filter(
                Q(id__in=simple_product_ids) | Q(id__in=variant_product_ids)
            )

        # Filter by stock availability
        if in_stock:
            simple_product_ids = models.SimpleProduct.objects.filter(stock__gt=0).values_list('product_id', flat=True)
            variant_product_ids = VariantProduct.objects.filter(stock__gt=0).values_list('product_id', flat=True)
            products = products.filter(
                Q(id__in=simple_product_ids) | Q(id__in=variant_product_ids)
            )

         # Prepare data for response
        all_search_items = []
        for product in products:
            if product.product_type == 'variant':
                variants = VariantProduct.objects.filter(product=product)
                for variant in variants:
                    all_search_items.append({
                        'product': VariantProductSerializer(variant).data,  # Use VariantProductSerializer
                        'is_variant': True
                    })
            else:
                simple_products = models.SimpleProduct.objects.filter(product=product)
                for simple_product in simple_products:
                    all_search_items.append({
                        'product': SimpleProductSerializer(simple_product).data,  # Use SimpleProductSerializer
                        'is_variant': False
                    })


        # Categories for filtering
        categories = models.Category.objects.all()
        category_serializer = CategorySerializer(categories, many=True)

        return Response({
            "all_search_items": all_search_items,
            "categories": category_serializer.data,
            "search_title": search_title,
        }, status=status.HTTP_200_OK)