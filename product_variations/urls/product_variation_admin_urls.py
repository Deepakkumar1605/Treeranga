from django.urls import path
from product import views
from django.conf import settings
from product_variations.product_variations_views import product_variation_admin_views
from django.conf.urls.static import static


app_name = 'product_variations'



urlpatterns = [
    # variation admin
    path('variation/variation_add/', product_variation_admin_views.VariantionAdd.as_view(), name='variation_add'),
    path("variation/variation_list", product_variation_admin_views.VariationList.as_view(), name="variation_list"),
    path("variation/variation_update/<str:variation_id>", product_variation_admin_views.VariationUpdate.as_view(), name="variation_update"),
    path("variation/variation_delete/<str:variation_id>", product_variation_admin_views.VariationDelete.as_view(), name="variation_delete"),

    # attribute admin
    path('attributes/attributes_list', product_variation_admin_views.AttributeList.as_view(), name='attribute_list'),
    path('attributes/attributes_add/', product_variation_admin_views.AttributeAdd.as_view(), name='attribute_add'),
    path('attribute_update/<int:attribute_id>/', product_variation_admin_views.AttributeUpdate.as_view(), name='attribute_update'),
    path('attribute_delete/<int:attribute_id>/', product_variation_admin_views.AttributeDelete.as_view(), name='attribute_delete'),

    path('variant/<int:pk>/edit/', product_variation_admin_views.VariantProductUpdate.as_view(), name='product_variant_edit'),
    path('variant/<int:pk>/delete/', product_variation_admin_views.VariantProductDelete.as_view(), name='product_variant_delete'),
    path('variants/', product_variation_admin_views.VariantProductList.as_view(), name='variant_product_list'),
]   

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)