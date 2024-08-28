from decimal import Decimal
from django.db import models
import io
from PIL import Image
import os
import uuid
from django.core.files import File
from django.core.files.base import ContentFile
from helpers import utils
from django.template.defaultfilters import slugify
from users.models import User


def document_path(self, filename):
    basefilename, file_extension= os.path.splitext(filename)
    myuuid = uuid.uuid4()
    return 'files/{basename}{randomstring}{ext}'.format(basename= basefilename, randomstring= str(myuuid), ext= file_extension)
class Category(models.Model):
    title=models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    image = models.ImageField(upload_to='category/', blank=True, null=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)



class Products(models.Model):
    YESNO = (
        ("yes", "yes"),
        ("no", "no")
    )

    PRODUCT_TYPE_CHOICES = [
        ('simple', 'Simple Product'),
        ('variant', 'Variant Product'),
    ]

    GST_CHOICES = [
        (Decimal('0.00'), '0%'),
        (Decimal('5.00'), '5%'),
        (Decimal('12.00'), '12%'),
        (Decimal('18.00'), '18%'),
        (Decimal('28.00'), '28%'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    uid = models.CharField(max_length=255, null=True, blank=True)
    sku_no = models.CharField(max_length=255, null=True, blank=True, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True, unique=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='product_image/', null=True, blank=True)
    product_short_description = models.TextField(null=True, blank=True)
    product_long_description = models.TextField(null=True, blank=True)
    trending = models.CharField(max_length=255, choices=YESNO, default="no")
    show_as_new = models.CharField(max_length=255, choices=YESNO, default="no")
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='simple')

    # GST Fields
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, choices=GST_CHOICES, default=Decimal('0.00'))
    sgst = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), editable=False)
    cgst = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), editable=False)

    def save(self, *args, **kwargs):
        if self.gst_rate is not None:
            # Calculate SGST and CGST by dividing the GST rate by 2
            half_gst = self.gst_rate / 2
            self.sgst = half_gst
            self.cgst = half_gst

        # Call the parent class's save method
        super(Products, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class SimpleProduct(models.Model):
    product = models.ForeignKey('Products', on_delete=models.CASCADE, null=True, blank=True)
    product_max_price = models.FloatField(default=0.0, null=True, blank=True)
    product_discount_price = models.FloatField(default=0.0, null=True, blank=True)
    stock = models.IntegerField(default=1, blank=True, null=True)
    taxable_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False)
    flat_delivery_fee = models.BooleanField(default=False)
    virtual_product = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Ensure the related product exists and has a gst_rate
        if self.product and self.product.gst_rate is not None:
            # Calculate the taxable value
            discount_price = Decimal(self.product_discount_price)
            total_gst = discount_price * (self.product.gst_rate / 100)
            self.taxable_value = discount_price - total_gst

        # Call the parent class's save method
        super(SimpleProduct, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - Simple Product"

class ImageGallery(models.Model):
    simple_product = models.ForeignKey(SimpleProduct, on_delete=models.CASCADE, related_name='image_gallery')
    images = models.JSONField(default=list, null=True, blank=True)
    video = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return f"Gallery for {self.simple_product.product}"


class DeliverySettings(models.Model):
    delivery_charge_per_bag = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_free_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return "Delivery Settings"



class ProductReview(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1)  # Rating out of 5
    review = models.TextField(null=True, blank=True)
    approved = models.BooleanField(default=False)  # Admin approval required
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review by {self.user.username} on {self.product.name}'