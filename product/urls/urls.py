from django.urls import path
from product import views
from django.conf import settings
from product.product_views import admin_product_views,user_product_views
from django.conf.urls.static import static


app_name = 'product'



urlpatterns = [
    # catagory admin
    path('Catagory/CatagoryAdd/', admin_product_views.CatagoryAdd.as_view(), name='category_add'),
    path("Catagory/CatagoryList", admin_product_views.CategoryList.as_view(), name="category_list"),
    path("Catagory/Catagoryupdate/<str:category_id>", admin_product_views.CategoryUpdate.as_view(), name="category_update"),
    path("Catagory/CatagoryDelete/<str:catagory_id>", admin_product_views.CatagotyDelete.as_view(), name="catagory_delete"),

    #product web admin
    path("ProductAdd", admin_product_views.ProductAdd.as_view(), name="product_add"),
    path('ProductEdit/<int:pk>/', admin_product_views.ProductEdit.as_view(), name='product_edit'),
    path("ProductList", admin_product_views.ProductList.as_view(), name="product_list"),
    path("ProductSearch", admin_product_views.ProductSearch.as_view(), name="product_search"),
    path("ProductFilter", admin_product_views.ProductFilter.as_view(), name="product_filter"),
    path('AdminProductReviews&Ratings/', admin_product_views.AdminReviewManagementView.as_view(), name='admin_review_management'),
    
    #simple product
    path("SimpleProductList", admin_product_views.SimpleProductList.as_view(), name="simple_product_list"),
    path("SimpleProductUpdate/<int:pk>", admin_product_views.SimpleProductUpdate.as_view(), name="simple_product_update"),
    path("SimpleProductDelete/<int:pk>", admin_product_views.SimpleProductDelete.as_view(), name="simple_product_delete"),
    path("SimpleProductSearch", admin_product_views.SimpleProductSearch.as_view(), name="simple_product_search"),

    # product web user
    path('category/<str:category_name>/', user_product_views.ShowProductsView.as_view(), name='products_of_category'),
    path('Product/<int:p_id>/', user_product_views.ProductDetailsView.as_view(), name='product_detail'),
    path('New-Products/', user_product_views.AllNewProductsView.as_view(), name='all_new_products'),
    path('Trending-Products/', user_product_views.AllTrendingProductsView.as_view(), name='all_trending_products'),
    
    path('mens/collections-Products/', user_product_views.MensProductsView.as_view(), name='mens_products'),
    path('womens/collections-Products/', user_product_views.WoMensProductsView.as_view(), name='womens_products'),
    path('boys/collections-Products/', user_product_views.BoyProductsView.as_view(), name='boys_products'),
    
    path('redirect-to-variant/', user_product_views.VariantRedirectView.as_view(), name='redirect_to_variant'),
    path('search_products/', user_product_views.search_product_names, name='search_product_names'),
    path('search/', user_product_views.SearchItems.as_view(), name='search_items'),
    # delivery charge settings
    path('UpdateDeliverySettings/', admin_product_views.DeliverySettingsUpdateView.as_view(), name='update_delivery_settings'),

    # path('get-variant-types/', admin_product_views.get_variant_types, name='get_variant_types'),
    path('get-attributes/<int:variant_type_id>', admin_product_views.get_attributes, name='get_attributes'),
    path('generate-combinations/', admin_product_views.generate_combinations, name='generate_combinations'),
    path('save-combination/', admin_product_views.save_combination, name='save_combination'),

]   

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
