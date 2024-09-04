from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from product.models import Products,SimpleProduct,ImageGallery

from wishlist.models import WishList

def add_to_wishlist(request):
    if request.method == 'GET':
        user = request.user
        product_name = request.GET.get('prod_name')
        
        product = get_object_or_404(Products, name=product_name)
        
        wishlist, created = WishList.objects.get_or_create(user=user)
        
        product_key = str(product.id)
        
        if product_key not in wishlist.products:
            wishlist.products[product_key] = {
                'name': product.name,
                'image': product.image.url,  # Assuming your product has an image field
                'price': product.simpleproduct.product_discount_price  # Adjust based on your model structure
            }
            wishlist.save()
        
        return redirect("shoppingsite:wishlist_products")



def remove_from_wishlist(request):
    if request.method == 'GET':
        user = request.user
        product_name = request.GET.get('prod_name')
        
        product = get_object_or_404(Products, name=product_name)
        product_key = str(product.id)
        
        try:
            wishlist = WishList.objects.get(user=user)
            products = wishlist.products
            
            if product_key in products:
                del products[product_key]
                wishlist.save()
                return redirect("shoppingsite:wishlist_products")
            else:
                return JsonResponse({'status': 'Product not found in wishlist'}, status=400)

        except WishList.DoesNotExist:
            return JsonResponse({'status': 'Wishlist does not exist for this user'}, status=400)

    return JsonResponse({'status': 'Invalid request method or not AJAX'}, status=400)

class AllWishListProducts(View):
    template_name = 'wishlist/wishlist_items.html'

    def get(self, request):
        user = request.user
        try:
            wishlist = WishList.objects.get(user=user)
            products = wishlist.products

            prd_objs = []
            for product_id in list(products):
                prd_obj = Products.objects.filter(id=product_id).first()
                if prd_obj:
                    prd_objs.append(prd_obj)
                else:
                    # Remove product from wishlist if it doesn't exist
                    del products[product_id]

            wishlist.save()

            # Zip wishlist items with their corresponding Product objects
            wishlist_items = zip(products.values(), prd_objs)
        
            return render(request, self.template_name, {
                "wishlist_items": wishlist_items,
                "MEDIA_URL": settings.MEDIA_URL
            })

        except WishList.DoesNotExist:
            return render(request, self.template_name, {
                "wishlist_items": [],
                "MEDIA_URL": settings.MEDIA_URL
            })
