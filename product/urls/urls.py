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

    #product web admin
    path("product/product_add", admin_product_views.ProductAdd.as_view(), name="product_add"),
    path('product/edit/<int:pk>/', admin_product_views.ProductEdit.as_view(), name='product_edit'),
    path("product/product_list", admin_product_views.ProductList.as_view(), name="product_list"),
    path("product/product_search", admin_product_views.ProductSearch.as_view(), name="product_search"),
    path("product/product_filter", admin_product_views.ProductFilter.as_view(), name="product_filter"),
    path('admin/review_approval/', admin_product_views.AdminReviewApprovalView.as_view(), name='review_approval'),
    
    #simple product
    path("simple_product/simple_product_list", admin_product_views.SimpleProductList.as_view(), name="simple_product_list"),
    path("simple_product/simple_product_update/<int:pk>", admin_product_views.SimpleProductUpdate.as_view(), name="simple_product_update"),
    path("simple_product/simple_product_delete/<int:pk>", admin_product_views.SimpleProductDelete.as_view(), name="simple_product_delete"),
    path("simple_product/simple_product_search", admin_product_views.SimpleProductSearch.as_view(), name="simple_product_search"),

    # product web user
    path('category/<str:category_name>/', user_product_views.ShowProductsView.as_view(), name='products_of_category'),
    path('product/<int:p_id>/', user_product_views.ProductDetailsSmipleView.as_view(), name='product_detail'),
    path('new-products/', user_product_views.AllNewProductsView.as_view(), name='all_new_products'),
    path('trndong-products/', user_product_views.AllTrendingProductsView.as_view(), name='all_trending_products'),

    path('update-delivery-settings/', admin_product_views.DeliverySettingsUpdateView.as_view(), name='update_delivery_settings'),


]   

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
