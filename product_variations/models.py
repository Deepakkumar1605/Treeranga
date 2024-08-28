from django.db import models

from product.models import Products, SimpleProduct


class ProductVariation(models.Model):
    parent_product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='variations')
    variation_attributes = models.JSONField(default=dict)  # Store attributes as key-value pairs, e.g., {"size": "L", "color": "Red"}
    product_max_price = models.FloatField(default=0.0, null=True, blank=True)
    product_discount_price = models.FloatField(default=0.0, null=True, blank=True)
    stock = models.IntegerField(default=1, blank=True, null=True)

    def __str__(self):
        parent_name = self.parent_product.name if self.parent_product else "No Parent"
        return f"{parent_name} - {', '.join([f'{k}: {v}' for k, v in self.variation_attributes.items()])}"

class ProductAttribute(models.Model):
    name = models.CharField(max_length=100)  # Attribute name, e.g., "Size"
    value = models.CharField(max_length=255)  # Attribute value, e.g., "L"
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='attributes')

    def __str__(self):
        return f"{self.name}: {self.value}"
    