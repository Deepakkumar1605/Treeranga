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
        product_id = request.GET.get('product_id')
        is_variant = request.GET.get('is_variant', 'false') == 'true'

        # Fetch or create the wishlist for the user
        wishlist, created = WishList.objects.get_or_create(user=user)

        # Handle variant products
        if is_variant:
            product = VariantProduct.objects.filter(pk=product_id).first()
            if not product:
                return JsonResponse({'status': 'VariantProduct not found'}, status=404)
            # Store VariantProduct ID
            stored_product_id = product.id
        else:
            # Handle simple products
            product = SimpleProduct.objects.filter(pk=product_id).first()
            if not product:
                return JsonResponse({'status': 'SimpleProduct not found'}, status=404)
            # Store SimpleProduct ID
            stored_product_id = product.id

        # Ensure products field is a dictionary
        if not isinstance(wishlist.products, dict):
            wishlist.products = {}

        # Add product details to the wishlist using the correct product type ID
        wishlist.products[stored_product_id] = {
            "name": product.product.name if hasattr(product, 'product') else product.name,
            "discount_price": product.product_discount_price,
            "is_variant": is_variant,
        }
        wishlist.save()

        return JsonResponse({'status': 'Product added to wishlist'}, status=200)


def remove_from_wishlist(request):
    if request.method == 'GET':
        user = request.user
        product_id = request.GET.get('product_id')
        is_variant = request.GET.get('is_variant', 'false') == 'true'

        try:
            wishlist = WishList.objects.get(user=user)

            # Check if the product exists in the wishlist
            if product_id in wishlist.products:
                # Remove the product from the wishlist
                del wishlist.products[product_id]
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

            # Fetch both SimpleProduct and VariantProduct
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
