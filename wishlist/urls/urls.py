   
   
from django.urls import path
from product import views
from django.conf import settings
from wishlist.wishlist_views import admin_wishlist_views,user_wishlist_views
from django.conf.urls.static import static


app_name = 'wishlist'



   
urlpatterns=[ 
            path('add-to-wishlist/', user_wishlist_views.add_to_wishlist, name='add_to_wishlist'),
            path('remove-from-wishlist/', user_wishlist_views.remove_from_wishlist, name='remove_from_wishlist'),
            path('wishlist-products/', user_wishlist_views.AllWishListProducts.as_view(), name='wishlist_products'),
   ]