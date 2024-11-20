from django.urls import path
from product import views
from django.conf import settings
from coupons.coupons_views import admin_coupon_views, user_coupon_views
from django.conf.urls.static import static

app_name = 'coupons'

urlpatterns = [
    # catagory admin
    path('Coupon/CouponAdd/', admin_coupon_views.CouponAdd.as_view(), name='coupon_add'),
    path("Coupon/CouponList", admin_coupon_views.CouponList.as_view(), name="coupon_list"),
    path("Coupon/Couponupdate/<str:coupon_id>", admin_coupon_views.CouponUpdate.as_view(), name="coupon_update"),
    path("Coupon/CouponDelete/<str:coupon_id>", admin_coupon_views.CouponDelete.as_view(), name="coupon_delete"),
    
    
    path('coupon/', user_coupon_views.Getcoupons.as_view(), name='all_coupons'),

]   

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
