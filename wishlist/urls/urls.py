   
from django.urls import path
from product import views
from django.conf import settings
from wishlist.wishlist_views import api_wishlist_views,user_wishlist_views
from django.conf.urls.static import static


app_name = 'wishlist'
   
urlpatterns = [
    # User Wishlist Views
    path('wishlist/add/', user_wishlist_views.AddToWishlistView.as_view(), name='add_to_wishlist'),
    path('wishlist/remove/', user_wishlist_views.RemoveFromWishlistView.as_view(), name='remove_from_wishlist'),
    path('wishlist/', user_wishlist_views.AllWishlistItemsView.as_view(), name='wishlist_items'),

    # API Wishlist Views
    path('api/wishlist/add/', api_wishlist_views.AddToWishlistAPIView.as_view(), name='api_add_to_wishlist'),
    path('api/wishlist/remove/', api_wishlist_views.RemoveFromWishlistAPIView.as_view(), name='api_remove_from_wishlist'),
    path('api/wishlist/', api_wishlist_views.AllWishlistItemsAPIView.as_view(), name='api_all_wishlist_items'),
]
