from django.urls import path
from cart.cart_views import api_cart_views

from django.contrib.auth import views 

app_name = 'cart'

urlpatterns = [
    path('api/showcart/', api_cart_views.ShowCartAPIView.as_view(), name='show-cart-api'),
    path('api/showcart/', api_cart_views.ShowCartAPIView.as_view(), name='show-cart-api'),
    path('api/add-to-cart/<int:product_id>/', api_cart_views.AddToCartAPIView.as_view(), name='add-to-cart-api'),


]