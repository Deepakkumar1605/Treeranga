from django.urls import path
from product.product_views import api_product_views

from django.contrib.auth import views 

app_name = 'product'

urlpatterns = [
    path('api/categories/', api_product_views.CategoryListAPIView.as_view(), name='category-list'),
    path('api/product/<int:p_id>/', api_product_views.ProductDetailsApiView.as_view(), name='product-details-api'),
    path('api/trending-products/', api_product_views.AllTrendingProductsAPIView.as_view(), name='all-trending-products-api'),
    path('api/new-products/', api_product_views.AllNewProductsAPIView.as_view(), name='all-new-products-api'),
    path('api/products/<str:category_name>/', api_product_views.ShowProductsAPIView.as_view(), name='show_products_api'),
    path('api/search-product-names/', api_product_views.SearchProductNamesAPIView.as_view(), name='search-product-names'),
    path('api/search-items/', api_product_views.SearchItemsAPIView.as_view(), name='search-items'), 
    path('api/products/<int:p_id>/review/', api_product_views.ProductReviewAPIView.as_view(), name='product_review_api'),
    path('api/products/', api_product_views.ShowAllProductsAPIView.as_view(), name='api_all_products'),

]