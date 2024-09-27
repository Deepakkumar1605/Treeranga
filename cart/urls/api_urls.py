from django.urls import path
from cart.cart_views import api_cart_views

from django.contrib.auth import views 

app_name = 'cart'

urlpatterns = [
    path('api/showcart/', api_cart_views.ShowCartAPIView.as_view(), name='show-cart-api'),
    path('api/add-to-cart/<int:product_id>/', api_cart_views.AddToCartAPIView.as_view(), name='add-to-cart-api'),

    path('api/manage_cart/<str:c_p_uid>/', api_cart_views.ManageCartAPIView.as_view(), name='manage-cart-api'),
    path('api/remove/<str:cp_uid>/', api_cart_views.RemoveFromCartAPIView.as_view(), name='remove_from_cart_api'),
    path('api/checkout/', api_cart_views.CheckoutAPIView.as_view(), name='checkout_api'),

    path('api/apply/', api_cart_views.ApplyCouponAPIView.as_view(), name='apply_coupon'),
    path('api/remove/', api_cart_views.RemoveCouponAPIView.as_view(), name='remove_coupon'),


]