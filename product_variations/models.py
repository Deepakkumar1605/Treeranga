from decimal import Decimal
from django.db import models

from product.models import Products, SimpleProduct

class Variant(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

class Attribute(models.Model):
    variant_type = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=100, null=True, blank=True)
 
    def __str__(self):
        return f"{self.variant_type}-{self.name}-{self.code}"

class VariantProduct(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, null=True, blank=True)
    variant_combination = models.JSONField(null=True, blank=True)
    product_max_price = models.FloatField(default=0.0, null=True, blank=True)
    product_discount_price = models.FloatField(default=0.0, null=True, blank=True)    
    stock = models.IntegerField(default=1, blank=True, null=True)
    taxable_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    is_visible = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.product and self.product.gst_rate is not None:
            discount_price = Decimal(self.product_discount_price)
            total_gst = discount_price * (self.product.gst_rate / 100)
            self.taxable_value = discount_price - total_gst

        super(VariantProduct, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name}"

class VariantImageGallery(models.Model):
    variant_product = models.ForeignKey(VariantProduct, on_delete=models.CASCADE, related_name='image_gallery')
    images = models.JSONField(default=list, null=True, blank=True)
    video = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return f"Gallery for {self.variant_product.product}"