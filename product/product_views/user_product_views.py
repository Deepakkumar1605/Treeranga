from django.shortcuts import render, get_object_or_404,redirect
from django.views import View
from app_common import models
from django.contrib import messages
from product.models import Products, Category,SimpleProduct,ImageGallery,ProductReview
from django.db.models import Avg
from wishlist.models import WshList
from product.forms import ProductReviewForm
from django.conf import settings

app = 'product/'

class ShowProductsView(View):
    template = app + 'user/productofcategory.html'

    def get(self, request, category_name):
        user = request.user

        # Get the category object for the given category_name
        category_obj = get_object_or_404(Category, title=category_name)

        # Get products for this category
        products_for_this_category = Products.objects.filter(
            category=category_obj
        )

        simple_products = []
        for product in products_for_this_category:
            simple_products_for_product = SimpleProduct.objects.filter(product=product)
            for simple_product in simple_products_for_product:
                image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                images = image_gallery.images if image_gallery else []
                videos = image_gallery.video if image_gallery else []
                simple_products.append({
                    'product': product,
                    'simple_product': simple_product,
                    'images': images,
                    'videos': videos
                })

        return render(request, self.template, {
            'simple_products': simple_products,
            'category_obj': category_obj,
            'user': user,
            "MEDIA_URL": settings.MEDIA_URL,
        })

class ProductDetailsSmipleView(View):
    template_name = app + 'user/product_details.html'

    def get(self, request, p_id):
        user = request.user
        category_obj = Category.objects.all()
        product_obj = get_object_or_404(Products, id=p_id)
        similar_product_list = Products.objects.filter(category=product_obj.category).exclude(id=product_obj.id)[:5]

        # Fetch the SimpleProduct instances for similar products
        similar_simple_products = []
        for product in similar_product_list:
            simple_product = SimpleProduct.objects.filter(product=product).first()
            if simple_product:
                similar_simple_products.append({
                    'product': product,
                    'simple_product': simple_product
                })

        # Get the first SimpleProduct for the current product
        simple_product = SimpleProduct.objects.filter(product=product_obj).first()
        image_gallery = None
        if simple_product:
            image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()

        wishlist_items = []
        if user.is_authenticated:
            wishlist = WshList.objects.filter(user=user).first()
            wishlist_items = wishlist.products.all() if wishlist else []

        context = {
            'user': user,
            'category_obj': category_obj,
            'product_obj': product_obj,
            'simple_product': simple_product,
            'image_gallery': image_gallery,
            'similar_simple_products': similar_simple_products,
            'wishlist_items': wishlist_items,
            'MEDIA_URL': settings.MEDIA_URL,
        }

        return render(request, self.template_name, context) 


class AllTrendingProductsView(View):
    template_name = app + 'user/trending_products.html'

    def get(self, request):
        trending_products = Products.objects.filter(trending="yes")
        
        context = {
            'trending_products': trending_products,
            'MEDIA_URL': settings.MEDIA_URL,
        }
        return render(request, self.template_name, context)



class AllNewProductsView(View):
    template_name = app + "user/new_product.html"

    def get(self, request):
        new_products = Products.objects.filter(show_as_new="yes")
        
        context = {
            'new_products': new_products,
            'MEDIA_URL': settings.MEDIA_URL,
        }
        return render(request, self.template_name, context)

