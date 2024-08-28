from django.urls import path
from product import views
from django.conf import settings
from cart.cart_views import user_cart_views
from django.conf.urls.static import static


app_name = 'cart'

urlpatterns = [
    #cart&checkout
    path('show-cart/', user_cart_views.ShowCart.as_view(), name='showcart'),
    path('add-to-cart/<int:product_id>/', user_cart_views.AddToCartView.as_view(), name='addtocart'),
    path('manage-cart/<str:c_p_uid>/', user_cart_views.ManageCart.as_view(), name='managecart'),
    path('remove-from-cart/<str:cp_uid>/', user_cart_views.RemoveFromCart, name='removefromcart'),
    path('checkout/',user_cart_views.Checkout.as_view(),name='checkout'),
    path('directbuychecout/<int:p_id>',user_cart_views.DirectBuyCheckout.as_view(),name='directbuycheckout'),


     # checkout address
    path('addaddress',user_cart_views.AddAddress.as_view(),name="addaddress"),
    path('update_address/', user_cart_views.update_address_view, name='update_address'),
    path('delete-address/<str:address_id>/', user_cart_views.DeleteAddress.as_view(), name='delete_address'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)