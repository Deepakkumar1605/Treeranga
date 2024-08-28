from django.urls import path
from product.product_views import api_product_views

from django.contrib.auth import views 

app_name = 'product'

urlpatterns = [
    path('api/categories/', api_product_views.CategoryListAPIView.as_view(), name='category-list'),
    path('api/categories/<str:category_name>/products/', api_product_views.ShowProductsAPIView.as_view(), name='show-products-api'),
    path('api/product/<int:p_id>/', api_product_views.ProductDetailsApiView.as_view(), name='product-details-api'),
    path('api/trending-products/', api_product_views.AllTrendingProductsAPIView.as_view(), name='all-trending-products-api'),
    path('api/new-products/', api_product_views.AllNewProductsAPIView.as_view(), name='all-new-products-api'),
]