from django.db import models
from users.models import User
from helpers import utils
class Order(models.Model):
    ORDER_STATUS = (
        ("Placed","Placed"),
        ("Accepted","Accepted"),
        ("Cancel","Cancel"),
        ("On_Way","On_Way"),
        ("Refund","Refund"),
        ("Return","Return"),
    )

    PaymentStatus = (
        ("Paid","Paid"),
        ("Pending","Pending"),
        ("Refunded","Refunded"),
    )

    PAYMENT_METHOD_CHOICES = (
        ('razorpay', 'Razorpay'),
        ('cod', 'Cash on Delivery'),
    )

    uid=models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name=models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True,blank=True)
    products = models.JSONField(default=dict, null=True, blank=True)
    coupon = models.CharField(max_length=255, null=True, blank=True)
    order_value = models.FloatField(default=0.0)
    order_meta_data = models.JSONField(default=dict, null=True, blank=True)
    order_status = models.CharField(max_length=255, choices= ORDER_STATUS, default="Placed")
    razorpay_payment_id = models.TextField(null= True, blank=True)
    razorpay_order_id = models.TextField(null= True, blank=True)
    razorpay_signature = models.TextField(null= True, blank=True)
    payment_status = models.CharField(max_length=255, choices= PaymentStatus, default="Paid")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='razorpay')
    address = models.JSONField(default=dict, null=True, blank=True)
    transaction_id = models.TextField(null= True, blank=True)
    date = models.DateField(auto_now_add= True, null=True, blank=True)

    can_edit = models.BooleanField(default=True) # id a order is canceled or refunded, make it non editable

    def __str__(self):
        return self.uid

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = utils.get_rand_number(5)
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    user_info = models.JSONField(default=dict, null=True, blank=True)  # Store user details as JSON
    product_info = models.JSONField(default=dict, null=True, blank=True)  # Store ordered product details as JSON
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.FloatField(default=0.0)  # Calculated based on product_info['price_per_unit'] * quantity

    def __str__(self):
        return f"OrderItem {self.id} for Order {self.order.uid}"

    def save(self, *args, **kwargs):
        if 'price_per_unit' in self.product_info:
            self.total_price = self.product_info['price_per_unit'] * self.quantity
        super().save(*args, **kwargs)