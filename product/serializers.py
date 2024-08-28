from rest_framework import serializers
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