from django.urls import path
from product import views
from django.conf import settings
from product.product_views import admin_product_views,user_product_views
from django.conf.urls.static import static


app_name = 'product'



urlpatterns = [
    # catagory admin
    path('catagory/catagory_add/', admin_product_views.CatagoryAdd.as_view(), name='category_add'),
    path("catagory/catagory_list", admin_product_views.CategoryList.as_view(), name="category_list"),
    path("catagory/catagory_update/<str:category_id>", admin_product_views.CategoryUpdate.as_view(), name="category_update"),
    path("catagory/catagory_delete/<str:catagory_id>", admin_product_views.CatagotyDelete.as_view(), name="catagory_delete"),


]   

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
