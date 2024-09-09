import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404,redirect,Http404
from django.urls import reverse
from django.views import View
from app_common import models
from django.contrib import messages
from product.models import Products, Category,SimpleProduct,ImageGallery,ProductReview
from django.db.models import Avg
from product.serializers import SimpleProductSerializer, VariantProductSerializer
from product_variations.models import Variant, VariantImageGallery, VariantProduct
from wishlist.models import WishList
from product.forms import ProductReviewForm
from django.conf import settings
from django.db.models import Q


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
                        'variant': "no",
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
                        'variant': "yes",
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

class ProductDetailsView(View):
    template_name = app + 'user/product_details.html'

    def get(self, request, p_id):
        user = request.user
        variant_param = request.GET.get('variant', '')

        # Check if the product is a SimpleProduct or VariantProduct
        print(f'p_id: {p_id}, variant_param: {variant_param}')
        
        product_obj = None
        product_type = None

        # Handle variant_param correctly
        if variant_param == "yes":
            try:
                product_obj = VariantProduct.objects.get(id=p_id)
                product_type = "variant"
            except VariantProduct.DoesNotExist:
                raise Http404("Product not found")
        else:
            try:
                product_obj = SimpleProduct.objects.get(id=p_id)
                product_type = "simple"
            except SimpleProduct.DoesNotExist:
                raise Http404("Product not found")

        category_obj = Category.objects.all()

        all_variants_of_this = []
        attributes = {}
        active_variant_attributes = {}
        product_images = []
        product_videos = []

        if product_obj:
            if product_type == "simple":
                image_gallery = ImageGallery.objects.filter(simple_product=product_obj).first()
                if image_gallery:
                    product_images = image_gallery.images
                    product_videos = image_gallery.video
            elif product_type == "variant":
                image_gallery = VariantImageGallery.objects.filter(variant_product=product_obj).first()
                if image_gallery:
                    product_images = image_gallery.images
                    product_videos = image_gallery.video
                
                avp = VariantProduct.objects.filter(product=product_obj.product)
                for av in avp:
                    variant_image_gallery = VariantImageGallery.objects.filter(variant_product=av).first()
                    variant_images = variant_image_gallery.images if variant_image_gallery else []
                    variant_videos = variant_image_gallery.video if variant_image_gallery else []
                    
                    all_variants_of_this.append({
                        'product': av,
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
            
            for attribute in attributes:
                attributes[attribute] = sorted(attributes[attribute])

        product_list_category_wise = Products.objects.filter(category=product_obj.product.category)
        all_simple_and_variant_similar = []

        for product in product_list_category_wise:
            if product.product_type == "simple":
                simple_product_similar = SimpleProduct.objects.filter(product=product, is_visible=True).exclude(id=product_obj.id)
                for simple_product in simple_product_similar:
                    image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                    similar_images = image_gallery.images if image_gallery else []
                    similar_videos = image_gallery.video if image_gallery else []
                    all_simple_and_variant_similar.append({
                        'product': simple_product,
                        'variant': "no",
                        'images': similar_images,
                        'videos': similar_videos
                    })
            elif product.product_type == "variant":
                variant_product_similar = VariantProduct.objects.filter(product=product, is_visible=True).exclude(id=product_obj.id).first()
                if variant_product_similar:
                    variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product_similar).first()
                    similar_images = variant_image_gallery.images if variant_image_gallery else []
                    similar_videos = variant_image_gallery.video if variant_image_gallery else []
                    all_simple_and_variant_similar.append({
                        'product': variant_product_similar,
                        'variant': "yes",
                        'images': similar_images,
                        'videos': similar_videos
                    })

        wishlist_items = []
        is_in_wishlist = False
        if user.is_authenticated:
            wishlist = WishList.objects.filter(user=user).first()
            wishlist_items = wishlist.products.all() if wishlist else []
            is_in_wishlist = str(product_obj.id) in [str(item.id) for item in wishlist_items]

        has_ordered_product = False
        if user.is_authenticated:
            orders = Order.objects.filter(user=user)
            for order in orders:
                products = order.products
                if str(product_obj.id) in products:
                    has_ordered_product = True
                    break

        form = ProductReviewForm()

        context = {
            'user': user,
            'category_obj': category_obj,
            'product_obj': product_obj,
            'all_variants_of_this': all_variants_of_this,
            'images': product_images,
            'videos': product_videos,
            'all_simple_and_variant_similar': all_simple_and_variant_similar,
            'wishlist_items': wishlist_items,
            'form': form,
            'MEDIA_URL': settings.MEDIA_URL,
            'variant_combination': product_obj.variant_combination if product_type == "variant" else None,
            'attributes': attributes,
            'active_variant_attributes': active_variant_attributes,
            'variant_param': variant_param
        }

        return render(request, self.template_name, context)

class VariantRedirectView(View):
    def get(self, request):
        attributes = request.GET.get('attributes', '{}')
        attributes = json.loads(attributes)
        product_id = request.GET.get('product_id', '')
        # Fetch the product
        product_obj = get_object_or_404(Products, id=product_id)

        # Fetch all variants for this product
        variants = VariantProduct.objects.filter(product=product_obj)

        # Filter variants based on selected attributes manually
        matching_variants = []
        for variant in variants:
            variant_combination = variant.variant_combination
            if all(variant_combination.get(attr) == val for attr, val in attributes.items()):
                matching_variants.append(variant)

        if matching_variants:
            first_variant = matching_variants[0]
            variant_url = f"{reverse('product:product_detail', kwargs={'p_id': first_variant.id})}?variant=yes"
            return JsonResponse({'redirect_url': variant_url})
        else:
            return JsonResponse({'error': 'No matching variant found'}, status=404)


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



class ProductSearchView(View):
    def post(self, request, *args, **kwargs):
        query = request.POST.get('search-box', '')
        suggestions = []
        if query:
            products = Products.objects.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query)
            ).values('id', 'name')[:5]  # Include product ID and name
            suggestions = list(products)
        return JsonResponse({'suggestions': suggestions})