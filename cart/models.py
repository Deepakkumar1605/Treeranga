from django.db import models
from users.models import User
from helpers import utils

class Cart(models.Model):
    uid=models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.JSONField(default=dict, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    total_price = models.IntegerField(default=0)

    def __str__(self):
        return self.uid

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = utils.get_rand_number(5)
        super().save(*args, **kwargs)
