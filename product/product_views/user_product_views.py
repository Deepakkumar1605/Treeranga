import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404,redirect,Http404
from django.urls import reverse
from django.views import View
from app_common import models
from django.contrib import messages
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
            if wishlist:
                wishlist_items = wishlist.products  # Inspect the structure of this variable
                print(f"wishlist_items: {wishlist_items}")  # Print to debug
                
                # Adjust this part based on the structure of wishlist_items
                is_in_wishlist = str(product_obj.id) in [str(item['id']) for item in wishlist_items] if isinstance(wishlist_items, list) else False

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




@login_required
@csrf_exempt  # Only for simplicity; ideally, use CSRF tokens with AJAX requests
def submit_review(request, product_type, product_id):
    # Get the product type and the specific product
    if product_type == 'simple':
        product = get_object_or_404(SimpleProduct, pk=product_id)
        content_type = ContentType.objects.get_for_model(SimpleProduct)
    elif product_type == 'variant':
        product = get_object_or_404(VariantProduct, pk=product_id)
        content_type = ContentType.objects.get_for_model(VariantProduct)
    else:
        return JsonResponse({'error': 'Invalid product type'}, status=400)

    # Check if the user has purchased this product by inspecting the products JSON in their orders
    has_purchased = Order.objects.filter(
        user=request.user,
        products__contains={'product_id': product_id}
    ).exists()

    if not has_purchased:
        return JsonResponse({'error': 'You can only review products you have purchased.'}, status=400)

    # Check if the user already reviewed this product
    existing_review = ProductReview.objects.filter(
        content_type=content_type, object_id=product_id, user=request.user
    ).first()

    if request.method == 'POST':
        form = ProductReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.content_type = content_type
            review.object_id = product.id
            review.save()
            return JsonResponse({'success': 'Your review has been submitted!'})
        else:
            return JsonResponse({'error': 'There was an error submitting your review.'}, status=400)

            
class AllTrendingProductsView(View):
    template_name = app + 'user/trending_products.html'

    def get(self, request):
        trending_products = Products.objects.filter(trending="yes")
        updated_trending_products = []

        for product in trending_products:
            # Check for simple products
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
            # Check for variant products
            elif product.product_type == "variant":
                variant_products = VariantProduct.objects.filter(product=product, is_visible=True)
                for variant_product in variant_products:
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




class AllNewProductsView(View):
    template_name = app + "user/new_product.html"

    def get(self, request):
        new_products = Products.objects.filter(show_as_new="yes")
        updated_new_products = []

        for product in new_products:
            # Check for simple products
            if product.product_type == "simple":
                simple_products = SimpleProduct.objects.filter(product=product, is_visible=True)
                for simple_product in simple_products:
                    image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first()
                    images = image_gallery.images if image_gallery else []
                    videos = image_gallery.video if image_gallery else []
                    updated_new_products.append({
                        'product': product,
                        'simple_product': simple_product,  # Pass simple product
                        'variant': "no",  # Indicate it's not a variant
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
                        'product': product,
                        'variant_product': variant_product,  # Pass variant product
                        'variant': "yes",  # Indicate it's a variant
                        'images': images,
                        'videos': videos
                    })

        context = {
            'new_products': updated_new_products,  # Pass updated products
            'MEDIA_URL': settings.MEDIA_URL,
        }
        return render(request, self.template_name, context)



def search_product_names(request):
    if request.method == 'POST':
        search_term = request.POST.get('search_term', '').strip()
        if search_term:
            products = Products.objects.filter(name__icontains=search_term).distinct('name')
            products_data = []

            for product in products:
                products_data.append({
                    'id': product.id,
                    'title': product.name,
                    'is_variant': "Yes" if product.product_type == 'variant' else "No"
                })

            return JsonResponse(products_data, safe=False)
    return JsonResponse([], safe=False)




class SearchItems(View):
    template_name = 'product/user/search_items.html'

    def get(self, request):
        search_title = request.GET.get("search_title", "").strip()
        if not search_title:
            return redirect("app_common:home")

        # Initial product query based on the search title
        products = Products.objects.filter(name__icontains=search_title)
        
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
            simple_product_ids = SimpleProduct.objects.filter(
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
                    all_search_items.append({
                        'product': variant,
                        'is_variant': True
                    })
            else:
                simple_products = SimpleProduct.objects.filter(product=product)
                for simple_product in simple_products:
                    all_search_items.append({
                        'product': simple_product,
                        'is_variant': False
                    })

        # Categories for filtering
        categories = Category.objects.all()

        # Pass the necessary data to the template
        context = {
            "all_search_items": all_search_items,
            "MEDIA_URL": settings.MEDIA_URL,
            "search_title": search_title,
            'categories': categories,
            'request': request,  # Pass request to access filters in the template
        }
        return render(request, self.template_name, context)
