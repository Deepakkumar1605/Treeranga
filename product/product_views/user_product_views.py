from django.shortcuts import render, get_object_or_404,redirect
from django.views import View
from app_common import models
from django.contrib import messages
from product.models import Products, Category,SimpleProduct,ImageGallery,ProductReview
from django.db.models import Avg
from product_variations.models import Variant, VariantImageGallery, VariantProduct
from wishlist.models import WshList
from product.forms import ProductReviewForm
from django.conf import settings

app = 'product/'

class ShowProductsView(View):
    template_name = app + 'user/productofcategory.html'

    def get(self, request, category_name):
        print(category_name)
        user = request.user
        category_obj = get_object_or_404(Category, title=category_name)
        print(category_obj)
        products_for_this_category = Products.objects.filter(category=category_obj)
        print(products_for_this_category)
        products_with_variants = []

        for product in products_for_this_category:
            if product.product_type == "simple":
                simple_products_for_product = SimpleProduct.objects.filter(product=product, is_visible=True)
                print(simple_products_for_product,"simple")
                for simple_product in simple_products_for_product:
                    image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                    images = image_gallery.images if image_gallery else []
                    videos = image_gallery.video if image_gallery else []
                    products_with_variants.append({
                        'product': product,
                        'simple_product': simple_product,
                        'variant_product': None,
                        'images': images,
                        'videos': videos
                    })
            elif product.product_type == "variant":
                variant_products = VariantProduct.objects.filter(product=product, is_visible=True)
                for variant_product in variant_products:
                    variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                    images = variant_image_gallery.images if variant_image_gallery else []
                    videos = variant_image_gallery.video if variant_image_gallery else []
                    products_with_variants.append({
                        'product': product,
                        'simple_product': None,
                        'variant_product': variant_product,
                        'images': images,
                        'videos': videos
                    })
        print(products_with_variants,"all Products")
        return render(request, self.template_name, {
            'products_with_variants': products_with_variants,
            'category_obj': category_obj,
            'user': user,
            "MEDIA_URL": settings.MEDIA_URL,
        })

class ProductDetailsSmipleView(View):
    template_name = app + 'user/product_details.html'

    def get(self, request, p_id):
        user = request.user
        product_obj = get_object_or_404(Products, id=p_id)
        category_obj = Category.objects.all()

        images = []
        videos = []
        simple_product = None
        variant_products = []  # List to hold all variant products for the product

        if product_obj.product_type == "simple":
            simple_product = SimpleProduct.objects.filter(product=product_obj, is_visible=True).first()
            if simple_product:
                image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                images = image_gallery.images if image_gallery else []
                videos = image_gallery.video if image_gallery else []
        elif product_obj.product_type == "variant":
            variant_products = VariantProduct.objects.filter(product=product_obj, is_visible=True)
            if variant_products.exists():
                variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_products.first()).first()
                images = variant_image_gallery.images if variant_image_gallery else []
                videos = variant_image_gallery.video if variant_image_gallery else []

        similar_product_list = Products.objects.filter(category=product_obj.category).exclude(id=product_obj.id)[:5]
        similar_products_with_variants = []

        for product in similar_product_list:
            if product.product_type == "simple":
                simple_product_similar = SimpleProduct.objects.filter(product=product, is_visible=True).first()
                if simple_product_similar:
                    similar_products_with_variants.append({
                        'product': product,
                        'simple_product': simple_product_similar,
                        'variant_product': None
                    })
            elif product.product_type == "variant":
                variant_product_similar = VariantProduct.objects.filter(product=product, is_visible=True).first()
                if variant_product_similar:
                    similar_products_with_variants.append({
                        'product': product,
                        'simple_product': None,
                        'variant_product': variant_product_similar
                    })

        wishlist_items = []
        if user.is_authenticated:
            wishlist = WshList.objects.filter(user=user).first()
            wishlist_items = wishlist.products.all() if wishlist else []

        context = {
            'user': user,
            'category_obj': category_obj,
            'product_obj': product_obj,
            'simple_product': simple_product,
            'variant_products': variant_products,
            'images': images,
            'videos': videos,
            'similar_products_with_variants': similar_products_with_variants,
            'wishlist_items': wishlist_items,
            'MEDIA_URL': settings.MEDIA_URL,
        }

        return render(request, self.template_name, context)





class AllTrendingProductsView(View):
    template_name = app + 'user/trending_products.html'

    def get(self, request):
        trending_products = Products.objects.filter(trending="yes")
        updated_trending_products = []
        for product in trending_products:
            if SimpleProduct.objects.filter(product=product, is_visible=True).exists():
                updated_trending_products.append(product)
        
        context = {
            'trending_products': updated_trending_products,
            'MEDIA_URL': settings.MEDIA_URL,
        }
        return render(request, self.template_name, context)



class AllNewProductsView(View):
    template_name = app + "user/new_product.html"

    def get(self, request):
        new_products = Products.objects.filter(show_as_new="yes")
        updated_new_products = []
        for product in new_products:
            if SimpleProduct.objects.filter(product=product, is_visible=True).exists():
                updated_new_products.append(product)
        context = {
            'new_products': updated_new_products,
            'MEDIA_URL': settings.MEDIA_URL,
        }
        return render(request, self.template_name, context)


