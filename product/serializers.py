from rest_framework import serializers

from product_variations.models import VariantImageGallery, VariantProduct
from .models import Category, ImageGallery, SimpleProduct, Products

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = '__all__'

class SimpleProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()

    class Meta:
        model = SimpleProduct
        fields = ['id', 'product', 'product_max_price', 'product_discount_price', 'stock', 'images', 'videos']

    def get_images(self, obj):
        # Fetch the ImageGallery for the SimpleProduct
        image_gallery = ImageGallery.objects.filter(simple_product=obj).first()
        # Return the list of image URLs from the JSON field
        return image_gallery.images if image_gallery else []

    def get_videos(self, obj):
        # Fetch the ImageGallery for the SimpleProduct
        video_gallery = ImageGallery.objects.filter(simple_product=obj).first()
        # Return the list of video URLs from the JSON field
        return video_gallery.video if video_gallery else []
    

class ImageGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageGallery
        fields = ['images', 'video']

class VariantImageGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantImageGallery
        fields = ['images', 'video']

class SimpleProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()

    class Meta:
        model = SimpleProduct
        fields = [
            'id',
            'product', 
            'product_max_price', 
            'product_discount_price', 
            'stock', 
            'taxable_value', 
            'flat_delivery_fee', 
            'virtual_product', 
            'is_visible',
            'images',   # Add images to the fields
            'videos'    # Add videos to the fields
        ]

    def get_images(self, obj):
        gallery = ImageGallery.objects.filter(simple_product=obj).first()
        return gallery.images if gallery else []

    def get_videos(self, obj):
        gallery = ImageGallery.objects.filter(simple_product=obj).first()
        return gallery.video if gallery else []

class VariantProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()

    class Meta:
        model = VariantProduct
        fields = [
            'id',
            'product', 
            'variant_combination',
            'product_max_price', 
            'product_discount_price', 
            'stock', 
            'taxable_value', 
            'is_visible',
            'images',   # Add images to the fields
            'videos'    # Add videos to the fields
        ]

    def get_images(self, obj):
        gallery = VariantImageGallery.objects.filter(variant_product=obj).first()
        return gallery.images if gallery else []

    def get_videos(self, obj):
        gallery = VariantImageGallery.objects.filter(variant_product=obj).first()
        return gallery.video if gallery else []

class ProductsSerializer(serializers.ModelSerializer):
    simple_products = SimpleProductSerializer(many=True, required=False)
    variant_products = VariantProductSerializer(many=True, required=False)

    class Meta:
        model = Products
        fields = ['id', 'name', 'product_type', 'simple_products', 'variant_products']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title']