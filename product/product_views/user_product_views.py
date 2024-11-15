import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404,redirect,Http404
from django.http import HttpResponseRedirect 
from django.urls import reverse
from django.views import View
from app_common import models
from django.contrib import messages
from app_common.error import render_error_page
from app_common.error import render_error_page
from orders.models import Order
from product.models import Products, Category,SimpleProduct,ImageGallery,ProductReview
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.csrf import csrf_exempt
from product.serializers import SimpleProductSerializer, VariantProductSerializer
from product_variations.models import Variant, VariantImageGallery, VariantProduct
from orders.models import Order
from wishlist.models import WishList
from product.forms import ProductReviewForm
from django.conf import settings
from django.db.models import Q
from orders.models import Order


app = 'product/'

class ShowProductsView(View):
    template_name = app + 'user/productofcategory.html'

    def get(self, request, category_name):
        try:
            user = request.user
            category_obj = get_object_or_404(Category, title=category_name)
            
            products_for_this_category = Products.objects.filter(category=category_obj)
            products_with_variants = []

            for product in products_for_this_category:
                if product.product_type == "simple":
                    simple_products_for_product = SimpleProduct.objects.filter(product=product, is_visible=True)
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

            return render(request, self.template_name, {
                'products_with_variants': products_with_variants,
                'category_obj': category_obj,
                'user': user,
                "MEDIA_URL": settings.MEDIA_URL,
            })

        except Category.DoesNotExist:
            error_message = "Category not found"
            return render_error_page(request, error_message, status_code=404)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

class ShowAllProductsView(View):
    template_name = app + 'user/all_products.html'

    def get(self, request):
        try:
            user = request.user
            all_products = Products.objects.all()
            products_with_variants = []

            for product in all_products:
                if product.product_type == "simple":
                    # Fetch simple product details and related images and videos
                    simple_products_for_product = SimpleProduct.objects.filter(product=product, is_visible=True)
                    for simple_product in simple_products_for_product:
                        image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                        images = image_gallery.images if image_gallery else []
                        videos = image_gallery.video if image_gallery else []
                        products_with_variants.append({
                            'product': product,
                            'simple_product': simple_product,
                            'is_variant': False,
                            'images': images,
                            'videos': videos
                        })
                elif product.product_type == "variant":
                    # Fetch variant product details and related images and videos
                    variant_products = VariantProduct.objects.filter(product=product, is_visible=True)
                    for variant_product in variant_products:
                        variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                        images = variant_image_gallery.images if variant_image_gallery else []
                        videos = variant_image_gallery.video if variant_image_gallery else []
                        products_with_variants.append({
                            'product': product,
                            'variant_product': variant_product,
                            'is_variant': True,
                            'images': images,
                            'videos': videos
                        })

            return render(request, self.template_name, {
                'products_with_variants': products_with_variants,
                'user': user,
                "MEDIA_URL": settings.MEDIA_URL,
            })

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)



class ProductDetailsView(View):
    template_name = app + 'user/product_details.html'

    def get(self, request, p_id):
        user = request.user
        variant_param = request.GET.get('variant', '')

        # Check if the product is a SimpleProduct or VariantProduct
        product_obj = None
        product_type = None

        # Handle variant_param correctly
        if variant_param == "yes":
            product_obj = VariantProduct.objects.get(id=p_id)
            product_type = "variant"
        else:
            product_obj = SimpleProduct.objects.get(id=p_id)
            product_type = "simple"

        # Get the parent Products object from SimpleProduct or VariantProduct
        parent_product = product_obj.product  # Assuming a ForeignKey 'product' in SimpleProduct/VariantProduct

        # Fetch reviews and calculate average rating for the parent product
        reviews = ProductReview.objects.filter(product=parent_product).order_by('-created_at')
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        average_rating = round(average_rating, 1)

        # Check if the user has purchased the product
        user_has_ordered = has_user_ordered_product(user, product_obj) if user.is_authenticated else False

        # Initialize review form
        form = ProductReviewForm(user=user)

        # Fetch category data and other product-related details
        category_obj = Category.objects.all()

        # Initialize variables for images, videos, variants, etc.
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

        # Fetch similar products
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

        # Check wishlist status
        wishlist_items = []
        is_added = False
        if user.is_authenticated:
            wishlist = WishList.objects.filter(user=user).first()
            if wishlist:
                products = wishlist.products.get('items', [])
                if any(str(item['id']) == str(p_id) and item['is_variant'] == variant_param for item in products):
                    is_added = True

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
            'variant_param': variant_param,
            'is_added': is_added,
            'reviews': reviews,
            'average_rating': average_rating,
            'star_range': range(1, 6),
            'user_has_ordered': user_has_ordered,
        }

        return render(request, self.template_name, context)

    def post(self, request, p_id):
    # Handle review form submission
        user = request.user
        variant_param = request.GET.get('variant', '')

        product_obj = get_object_or_404(VariantProduct if variant_param == "yes" else SimpleProduct, id=p_id)

        # Check if user has ordered the product before processing the form
        if not has_user_ordered_product(user, product_obj):
            messages.error(request, 'You can only review products you have purchased.')
            return HttpResponseRedirect(f"{reverse('product:product_detail', args=[p_id])}?variant={variant_param}")

        form = ProductReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.user = user
            review.product = product_obj.product  # Ensure you're saving the parent product
            review.save()
            messages.success(request, 'Thank you for your review!')
        else:
            messages.error(request, 'There was an error with your review submission.')

        return HttpResponseRedirect(f"{reverse('product:product_detail', args=[p_id])}?variant={variant_param}")

class VariantRedirectView(View):
    def get(self, request):
        try:
            # Retrieve and process query parameters
            attributes = request.GET.get('attributes', '{}')
            attributes = json.loads(attributes)
            product_id = request.GET.get('product_id', '')
            product_obj = get_object_or_404(Products, id=product_id)

            # Find matching variants
            variants = VariantProduct.objects.filter(product=product_obj)
            matching_variants = []
            for variant in variants:
                variant_combination = variant.variant_combination
                if all(variant_combination.get(attr) == val for attr, val in attributes.items()):
                    matching_variants.append(variant)

            # Determine redirect URL or return error
            if matching_variants:
                first_variant = matching_variants[0]
                variant_url = f"{reverse('product:product_detail', kwargs={'p_id': first_variant.id})}?variant=yes"
                return JsonResponse({'redirect_url': variant_url})
            else:
                return JsonResponse({'error': 'No matching variant found'}, status=404)
        
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return JsonResponse({'error': error_message}, status=400)

def has_user_ordered_product(user, product_obj):
    if not user.is_authenticated:
        return False
    orders = Order.objects.filter(user=user)
    for order in orders:
        products = order.products 
        for product_key, product_data in products.items():
            product_info = product_data.get('info', {})
            if str(product_info.get('product_id')) == str(product_obj.id):
                return True
    return False
# class AllTrendingProductsView(View):
#     template_name = app +'user/trending_products.html'

#     def get(self, request):
#         try:
#             trending_products = Products.objects.filter(trending="yes").order_by('-id')
#             updated_trending_products = []

#             for product in trending_products:
#                 if product.product_type == "simple":
#                     simple_products = SimpleProduct.objects.filter(product=product, is_visible=True)
#                     for simple_product in simple_products:
#                         image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
#                         images = image_gallery.images if image_gallery else []
#                         videos = image_gallery.video if image_gallery else []
#                         updated_trending_products.append({
#                             'product': product,
#                             'simple_product': simple_product,
#                             'variant': "no",
#                             'images': images,
#                             'videos': videos
#                         })
#                 elif product.product_type == "variant":
#                     variant_products = VariantProduct.objects.filter(product=product, is_visible=True).first()
#                     for variant_product in variant_products:
#                         variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
#                         images = variant_image_gallery.images if variant_image_gallery else []
#                         videos = variant_image_gallery.video if variant_image_gallery else []
#                         updated_trending_products.append({
#                             'product': product,
#                             'variant_product': variant_product,
#                             'variant': "yes",
#                             'images': images,
#                             'videos': videos
#                         })

#             context = {
#                 'trending_products': updated_trending_products,
#                 'MEDIA_URL': settings.MEDIA_URL,
#             }
#             return render(request, self.template_name, context)

#         except Exception as e:
#             error_message = f"An unexpected error occurred: {str(e)}"
#             return render_error_page(request, error_message, status_code=400)

class AllTrendingProductsView(View):
    template_name = app + 'user/trending_products.html'

    def get(self, request):
        try:
            trending_products = Products.objects.filter(trending="yes").order_by('-id')
            updated_trending_products = []

            for product in trending_products:
                if product.product_type == "simple":
                    simple_products = SimpleProduct.objects.filter(product=product, is_visible=True)
                    for simple_product in simple_products:
                        image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                        images = image_gallery.images if image_gallery else []
                        videos = image_gallery.video if image_gallery else []
                        updated_trending_products.append({
                            'product': product,
                            'simple_product': simple_product,
                            'variant': "no",
                            'images': images,
                            'videos': videos
                        })
                elif product.product_type == "variant":
                    variant_product = VariantProduct.objects.filter(product=product, is_visible=True).first()
                    if variant_product:
                        variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                        images = variant_image_gallery.images if variant_image_gallery else []
                        videos = variant_image_gallery.video if variant_image_gallery else []
                        updated_trending_products.append({
                            'product': product,
                            'variant_product': variant_product,
                            'variant': "yes",
                            'images': images,
                            'videos': videos
                        })

            context = {
                'trending_products': updated_trending_products,
                'MEDIA_URL': settings.MEDIA_URL,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
        
        
        
class MensProductsView(View):
    template_name = app + 'user/mens_collections.html'

    def get(self, request):
        try:
            trending_products = Products.objects.filter(product_for="Men").order_by('-id')
            updated_trending_products = []

            for product in trending_products:
                if product.product_type == "simple":
                    simple_products = SimpleProduct.objects.filter(product=product, is_visible=True)
                    for simple_product in simple_products:
                        image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                        images = image_gallery.images if image_gallery else []
                        videos = image_gallery.video if image_gallery else []
                        updated_trending_products.append({
                            'product': product,
                            'simple_product': simple_product,
                            'variant': "no",
                            'images': images,
                            'videos': videos
                        })
                elif product.product_type == "variant":
                    variant_product = VariantProduct.objects.filter(product=product, is_visible=True).first()
                    if variant_product:
                        variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                        images = variant_image_gallery.images if variant_image_gallery else []
                        videos = variant_image_gallery.video if variant_image_gallery else []
                        updated_trending_products.append({
                            'product': product,
                            'variant_product': variant_product,
                            'variant': "yes",
                            'images': images,
                            'videos': videos
                        })

            context = {
                'trending_products': updated_trending_products,
                'MEDIA_URL': settings.MEDIA_URL,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
        
        
class WoMensProductsView(View):
    template_name = app + 'user/Women_collections.html'

    def get(self, request):
        try:
            trending_products = Products.objects.filter(product_for="Women").order_by('-id')
            updated_trending_products = []

            for product in trending_products:
                if product.product_type == "simple":
                    simple_products = SimpleProduct.objects.filter(product=product, is_visible=True)
                    for simple_product in simple_products:
                        image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                        images = image_gallery.images if image_gallery else []
                        videos = image_gallery.video if image_gallery else []
                        updated_trending_products.append({
                            'product': product,
                            'simple_product': simple_product,
                            'variant': "no",
                            'images': images,
                            'videos': videos
                        })
                elif product.product_type == "variant":
                    variant_product = VariantProduct.objects.filter(product=product, is_visible=True).first()
                    if variant_product:
                        variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                        images = variant_image_gallery.images if variant_image_gallery else []
                        videos = variant_image_gallery.video if variant_image_gallery else []
                        updated_trending_products.append({
                            'product': product,
                            'variant_product': variant_product,
                            'variant': "yes",
                            'images': images,
                            'videos': videos
                        })

            context = {
                'trending_products': updated_trending_products,
                'MEDIA_URL': settings.MEDIA_URL,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
        
class BoyProductsView(View):
    template_name = app + 'user/boys_collections.html'

    def get(self, request):
        try:
            trending_products = Products.objects.filter(product_for="Women").order_by('-id')
            updated_trending_products = []

            for product in trending_products:
                if product.product_type == "simple":
                    simple_products = SimpleProduct.objects.filter(product=product, is_visible=True)
                    for simple_product in simple_products:
                        image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                        images = image_gallery.images if image_gallery else []
                        videos = image_gallery.video if image_gallery else []
                        updated_trending_products.append({
                            'product': product,
                            'simple_product': simple_product,
                            'variant': "no",
                            'images': images,
                            'videos': videos
                        })
                elif product.product_type == "variant":
                    variant_product = VariantProduct.objects.filter(product=product, is_visible=True).first()
                    if variant_product:
                        variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
                        images = variant_image_gallery.images if variant_image_gallery else []
                        videos = variant_image_gallery.video if variant_image_gallery else []
                        updated_trending_products.append({
                            'product': product,
                            'variant_product': variant_product,
                            'variant': "yes",
                            'images': images,
                            'videos': videos
                        })

            context = {
                'trending_products': updated_trending_products,
                'MEDIA_URL': settings.MEDIA_URL,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

# class AllNewProductsView(View):
#     template_name = app + 'user/new_product.html'
    

#     def get(self, request):
#         try:
#             new_products = Products.objects.filter(show_as_new="yes").order_by('id')
#             updated_new_products = []

#             for product in new_products:
#                 if product.product_type == "simple":
#                     simple_products = SimpleProduct.objects.filter(product=product, is_visible=True)
#                     for simple_product in simple_products:
#                         image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
#                         images = image_gallery.images if image_gallery else []
#                         videos = image_gallery.video if image_gallery else []
#                         updated_new_products.append({
#                             'product': product,
#                             'simple_product': simple_product,
#                             'variant': "no",
#                             'images': images,
#                             'videos': videos
#                         })
#                 elif product.product_type == "variant":
#                     variant_products = VariantProduct.objects.filter(product=product, is_visible=True).first()
#                     for variant_product in variant_products:
#                         variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_product).first()
#                         images = variant_image_gallery.images if variant_image_gallery else []
#                         videos = variant_image_gallery.video if variant_image_gallery else []
#                         updated_new_products.append({
#                             'product': product,
#                             'variant_product': variant_product,
#                             'variant': "yes",
#                             'images': images,
#                             'videos': videos
#                         })

#             context = {
#                 'new_products': updated_new_products,
#                 'MEDIA_URL': settings.MEDIA_URL,
#             }
#             return render(request, self.template_name, context)

#         except Exception as e:
#             error_message = f"An unexpected error occurred: {str(e)}"
#             return render_error_page(request, error_message, status_code=400)


class AllNewProductsView(View):
    template_name = app + 'user/new_product.html'
    
    def get(self, request):
        try:
            new_products = Products.objects.filter(show_as_new="yes").order_by('-id')
            updated_new_products = []

            for product in new_products:
                if product.product_type == "simple":
                    simple_products = SimpleProduct.objects.filter(product=product, is_visible=True)
                    for simple_product in simple_products:
                        image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                        images = image_gallery.images if image_gallery else []
                        videos = image_gallery.video if image_gallery else []
                        updated_new_products.append({
                            'product': product,
                            'simple_product': simple_product,
                            'variant': "no",
                            'images': images,
                            'videos': videos
                        })
                elif product.product_type == "variant":
                    variant_products = VariantProduct.objects.filter(product=product, is_visible=True).first()
                    if variant_products:
                        variant_image_gallery = VariantImageGallery.objects.filter(variant_product=variant_products).first()
                        images = variant_image_gallery.images if variant_image_gallery else []
                        videos = variant_image_gallery.video if variant_image_gallery else []
                        updated_new_products.append({
                            'product': product,
                            'variant_product': variant_products,
                            'variant': "yes",
                            'images': images,
                            'videos': videos
                        })

            context = {
                'new_products': updated_new_products,
                'MEDIA_URL': settings.MEDIA_URL,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

def search_product_names(request):
    try:
        if request.method == 'POST':
            search_term = request.POST.get('search_term', '').strip()
            if search_term:
                products = Products.objects.filter(name__icontains=search_term).distinct('name')
                products_data = []

                for product in products:
                    products_data.append({
                        'id': product.id,
                        'title': product.name,
                        'brand': product.brand,
                        
                        'is_variant': "Yes" if product.product_type == 'variant' else "No"
                    })

                return JsonResponse(products_data, safe=False)
        return JsonResponse([], safe=False)
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        return render_error_page(request, error_message, status_code=400)

class SearchItems(View):
    template_name = 'product/user/search_items.html'

    def get(self, request):
        try:
            search_title = request.GET.get("search_title", "").strip()
            if not search_title:
                return redirect("app_common:home")

            products = Products.objects.filter(name__icontains=search_title)

            # Get filter criteria from request
            category_id = request.GET.get('category')
            product_type = request.GET.get('product_type')
            min_price = request.GET.get('min_price')
            max_price = request.GET.get('max_price')
            in_stock = request.GET.get('in_stock')

            if category_id:
                products = products.filter(category_id=category_id)

            if in_stock:
                simple_product_ids = SimpleProduct.objects.filter(stock__gt=0).values_list('product_id', flat=True)
                variant_product_ids = VariantProduct.objects.filter(stock__gt=0).values_list('product_id', flat=True)
                products = products.filter(
                    Q(id__in=simple_product_ids) | Q(id__in=variant_product_ids)
                )

            all_search_items = []
            for product in products:
                if product.product_type == 'variant':
                    variants = VariantProduct.objects.filter(product=product)
                    for variant in variants:
                        # Get the first image from VariantImageGallery
                        image_gallery = VariantImageGallery.objects.filter(variant_product=variant).first()
                        main_image = image_gallery.images[0] if image_gallery and image_gallery.images else None
                        all_search_items.append({
                            'product': variant,
                            'is_variant': True,
                            'main_image': main_image
                        })
                else:
                    simple_products = SimpleProduct.objects.filter(product=product)
                    for simple_product in simple_products:
                        # Get the first image from ImageGallery
                        image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                        main_image = image_gallery.images[0] if image_gallery and image_gallery.images else None
                        all_search_items.append({
                            'product': simple_product,
                            'is_variant': False,
                            'main_image': main_image
                        })

            if min_price and max_price:
                all_search_items = [
                    item for item in all_search_items
                    if float(min_price) <= float(item['product'].product_discount_price) <= float(max_price)
                ]

            categories = Category.objects.all()

            context = {
                "all_search_items": all_search_items,
                "MEDIA_URL": settings.MEDIA_URL,
                "search_title": search_title,
                'categories': categories,
                'request': request,
            }
            return render(request, self.template_name, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)