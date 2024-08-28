from django.contrib import admin

from . import models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("id", "title__icontains")
    list_display = ("title", "id")

class SimpleProductInline(admin.TabularInline):
    model = models.SimpleProduct
    extra = 1
    fields = ['product_max_price', 'product_discount_price', 'stock']

class ImageGalleryInline(admin.TabularInline):
    model = models.ImageGallery
    extra = 3
    fields = ['images', 'videos']

@admin.register(models.Products)
class ProductsAdmin(admin.ModelAdmin):
    search_fields = ("name", "sku_no")
    list_display = ("name", "sku_no", "category", "product_type", "trending", "show_as_new")
    inlines = [SimpleProductInline]  # Inline for SimpleProduct

admin.site.register(models.SimpleProduct)
