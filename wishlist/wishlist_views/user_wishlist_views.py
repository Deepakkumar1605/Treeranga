from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from wishlist.models import WishList
from product.models import SimpleProduct,Products
from product_variations.models import VariantProduct
from django.views import View


def add_to_wishlist(request):
    if request.method == 'GET':
        user = request.user
        product_id = request.GET.get('product_id')  # Use the product id to fetch the product
        is_variant = request.GET.get('is_variant', 'false')  # Check if the product is a variant
        
        # Get the correct product (SimpleProduct or VariantProduct)
        if is_variant == 'true':
            product = get_object_or_404(VariantProduct, pk=product_id)
        else:
            product = get_object_or_404(SimpleProduct, pk=product_id)
        
        # Fetch or create the wishlist for the user
        wishlist, created = WishList.objects.get_or_create(user=user)
        
        # Ensure products field is a dictionary
        if not isinstance(wishlist.products, dict):
            wishlist.products = {}

        # Add product details to the wishlist (JSON structure)
        wishlist.products[product_id] = {
            "name": product.product.name,
            "discount_price": product.product_discount_price,
            "is_variant": is_variant,
        }
        wishlist.save()

        return redirect("wishlist:wishlist_products")


def remove_from_wishlist(request):
    if request.method == 'GET':
        user = request.user
        product_id = request.GET.get('product_id')  # Product id to remove
        
        try:
            wishlist = WishList.objects.get(user=user)
            if product_id in wishlist.products:
                del wishlist.products[product_id]  # Remove the product from the wishlist
                wishlist.save()

                return JsonResponse({'status': 'Product removed from wishlist'}, status=200)
            else:
                return JsonResponse({'status': 'Product not found in wishlist'}, status=404)

        except WishList.DoesNotExist:
            return JsonResponse({'status': 'Wishlist does not exist'}, status=404)



class AllWishListProducts(View):
    def get(self, request):
        user = request.user
        try:
            wishlist = WishList.objects.get(user=user)
            product_ids = wishlist.products.keys()
            prd_objs = []
            prd_is_variant = []

            # Retrieve products from both SimpleProduct and VariantProduct models
            for product_id in product_ids:
                product_data = wishlist.products[product_id]
                is_variant = product_data.get('is_variant', 'false') == 'true'

                if is_variant:
                    prd_obj = get_object_or_404(VariantProduct, pk=product_id)
                else:
                    prd_obj = get_object_or_404(SimpleProduct, pk=product_id)

                prd_objs.append(prd_obj)
                prd_is_variant.append(is_variant)

            wishlist_items = zip(wishlist.products.values(), prd_objs, prd_is_variant)

            return render(request, 'wishlist/user/wishlist_items.html', {
                "wishlist_items": wishlist_items,
                "MEDIA_URL": settings.MEDIA_URL
            })

        except WishList.DoesNotExist:
            return render(request, 'wishlist/user/wishlist_items.html', {
                "wishlist_items": [],
                "MEDIA_URL": settings.MEDIA_URL
            })

