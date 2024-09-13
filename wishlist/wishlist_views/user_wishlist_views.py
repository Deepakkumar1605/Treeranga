from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from wishlist.models import WishList
from product.models import SimpleProduct,Products
from product_variations.models import VariantProduct
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import json

class AddToWishlistView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            is_variant = data.get('is_variant')
            if not product_id:
                return JsonResponse({"error": "Product ID is required"}, status=400)

            if is_variant == "yes":
                product = get_object_or_404(VariantProduct, id=product_id)
            else:
                product = get_object_or_404(SimpleProduct, id=product_id)

            wishlist, created = WishList.objects.get_or_create(user=request.user)

            products = wishlist.products.get('items', [])
        
            if not any(str(item['id']) == str(product_id) and item['is_variant'] == is_variant for item in products):
                products.append({
                    'id': product_id,
                    'is_variant': is_variant,
                    'product_name': product.product.name  # Adjust according to your model
                })
                wishlist.products['items'] = products
                wishlist.save()

            return JsonResponse({"message": "Product added to wishlist"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)



class RemoveFromWishlistView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')

            if not product_id:
                return JsonResponse({"error": "Product ID is required"}, status=400)

            wishlist = get_object_or_404(WishList, user=request.user)

            products = wishlist.products.get('items', [])
            wishlist.products['items'] = [item for item in products if str(item['id']) != str(product_id)]
            wishlist.save()

            return JsonResponse({"message": "Product removed from wishlist"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)


class AllWishlistItemsView(View):
    def get(self, request):
        wishlist, created = WishList.objects.get_or_create(user=request.user)
        product_items = wishlist.products.get('items', [])
        detailed_products = []

        for item in product_items:
            product_id = item['id']
            is_variant = item['is_variant']
            product_name = item['product_name']

            if is_variant == "yes":
                product = get_object_or_404(VariantProduct, id=product_id)
                product_price = product.product_discount_price
                product_max_price = product.product_max_price
                product_image = product.product.image.url
            else:
                simple_product = get_object_or_404(SimpleProduct, id=product_id)
                product_price = simple_product.product_discount_price
                product_max_price = simple_product.product_max_price
                product_image = simple_product.product.image.url if simple_product.product.image else None

            detailed_products.append({
                'id': product_id,
                'name': product_name,
                'price': product_price,
                'max_price': product_max_price,
                'image': product_image
            })
            print(detailed_products)
        context = {
            'wishlist_items': detailed_products
        }

        return render(request, 'wishlist/user/wishlist_items.html', context)
