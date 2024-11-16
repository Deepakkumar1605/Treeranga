from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('fixed', 'fixed'),
        ('percent', 'percent'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    discount_type = models.CharField(choices=DISCOUNT_TYPES, max_length=10)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        return self.is_active and self.valid_from <= timezone.now() <= self.valid_to
