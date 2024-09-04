from django.shortcuts import render, get_object_or_404,redirect
from django.views import View
from app_common import models
from django.contrib import messages
from product.models import Products, Category,SimpleProduct,ImageGallery,ProductReview
from django.db.models import Avg
from wishlist.models import WishList
from orders.models import Order
from product.forms import ProductReviewForm
from django.conf import settings

app = 'product/'

class ShowProductsView(View):
    template = app + 'user/productofcategory.html'

    def get(self, request, category_name):
        user = request.user
        category_obj = get_object_or_404(Category, title=category_name)
        products_for_this_category = Products.objects.filter(category=category_obj)
        simple_products = []
        for product in products_for_this_category:
            simple_products_for_product = SimpleProduct.objects.filter(product=product, is_visible=True)
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
        product = get_object_or_404(Products, id=p_id)
        simple_product = SimpleProduct.objects.filter(product=product, is_visible=True).first()
        image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first() if simple_product else None
        reviews = ProductReview.objects.filter(product=product).order_by('-created_at')
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        average_rating = round(average_rating, 1)

        similar_product_list = Products.objects.filter(category=product.category).exclude(id=product.id)[:5]
        similar_simple_products = []
        for similar_product in similar_product_list:
            try:
                simple = SimpleProduct.objects.get(product=similar_product, is_visible=True)
                similar_simple_products.append({
                    'product': similar_product,
                    'simple_product': simple
                })
            except SimpleProduct.DoesNotExist:
                continue

        wishlist_items = []
        is_in_wishlist = False
        if user.is_authenticated:
            wishlist = WishList.objects.filter(user=user).first()
            wishlist_items = wishlist.products.all() if wishlist else []
            is_in_wishlist = str(product.id) in [str(item.id) for item in wishlist_items]
        # Check if the user has ordered the product
        has_ordered_product = False
        if user.is_authenticated:
            # Fetch all orders for the user
            orders = Order.objects.filter(user=user)
            for order in orders:
                products = order.products
                # Check if the product_id exists in the products JSON field
                if str(product.id) in products:
                    has_ordered_product = True
                    break

        form = ProductReviewForm()

        context = {
            'user': user,
            'category_obj': category_obj,
            'product_obj': product,
            'simple_product': simple_product,
            'image_gallery': image_gallery,
            'reviews': reviews,
            'average_rating': average_rating,
            'similar_simple_products': similar_simple_products,
            'wishlist_items': wishlist_items,
            'form': form,
            'MEDIA_URL': settings.MEDIA_URL,
            'star_range': range(1, 6),
            'has_ordered_product': has_ordered_product,
        }

        return render(request, self.template_name, context)

    def post(self, request, p_id):
        product = get_object_or_404(Products, id=p_id)
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            # Ensure the user has ordered the product before allowing review
            has_ordered_product = False
            if request.user.is_authenticated:
                orders = Order.objects.filter(user=request.user)
                for order in orders:
                    products = order.products
                    if str(product.id) in products:
                        has_ordered_product = True
                        break
            
            if has_ordered_product:
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                messages.success(request, "Your review has been submitted and is awaiting approval.")
                return redirect('product:product_detail', p_id=p_id)
            else:
                messages.error(request, "You must have ordered this product before leaving a review.")
        else:
            simple_product = SimpleProduct.objects.filter(product=product, is_visible=True).first()
            image_gallery = ImageGallery.objects.filter(simple_product=simple_product).first() if simple_product else None
            reviews = ProductReview.objects.filter(product=product).order_by('-created_at')
            average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            average_rating = round(average_rating, 1)

            similar_product_list = Products.objects.filter(category=product.category).exclude(id=product.id)[:5]
            similar_simple_products = []
            for similar_product in similar_product_list:
                try:
                    simple = SimpleProduct.objects.get(product=similar_product, is_visible=True)
                    similar_simple_products.append({
                        'product': similar_product,
                        'simple_product': simple
                    })
                except SimpleProduct.DoesNotExist:
                    continue

            wishlist_items = []
            if request.user.is_authenticated:
                wishlist = WishList.objects.filter(user=request.user).first()
                wishlist_items = wishlist.products.all() if wishlist else []

            context = {
                'user': request.user,
                'category_obj': Category.objects.all(),
                'product_obj': product,
                'simple_product': simple_product,
                'image_gallery': image_gallery,
                'reviews': reviews,
                'average_rating': average_rating,
                'similar_simple_products': similar_simple_products,
                'wishlist_items': wishlist_items,
                'form': form,
                'MEDIA_URL': settings.MEDIA_URL,
                'star_range': range(1, 6),
                'has_ordered_product': has_ordered_product,
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


