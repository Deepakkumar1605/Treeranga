from django.urls import path
from product import views
from django.conf import settings
from cart.cart_views import user_cart_views
from django.conf.urls.static import static


app_name = 'cart'

urlpatterns = [
    #cart&checkout
    path('Cart/', user_cart_views.ShowCart.as_view(), name='showcart'),
    path('AddToCart/<int:product_id>/', user_cart_views.AddToCartView.as_view(), name='addtocart'),
    path('ManageCart/<str:c_p_uid>/', user_cart_views.ManageCart.as_view(), name='managecart'),
    path('RemoveFromCart/<str:cp_uid>/', user_cart_views.RemoveFromCart, name='removefromcart'),
    path('checkout/',user_cart_views.Checkout.as_view(),name='checkout'),
    path('apply-coupon/', user_cart_views.ApplyCouponView.as_view(),name='apply_coupon'),
    path('remove-coupon/', user_cart_views.remove_coupon,name='remove_coupon'),


     # checkout address
    path('Addaddress',user_cart_views.AddAddress.as_view(),name="addaddress"),
    path('updateAddress/', user_cart_views.update_address_view, name='update_address'),
    path('DeleteAddress/<str:address_id>/', user_cart_views.DeleteAddress.as_view(), name='delete_address'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)