from django.db import models
from users.models import User
from helpers import utils


class ContactMessage(models.Model):
    uid=models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete= models.CASCADE, null= True, blank= True)
    name = models.CharField(max_length=255, null=True, blank=True)  # Added name field
    email = models.EmailField(null=True, blank=True)
    contact = models.CharField(max_length= 10, null=True, blank=True)
    message = models.TextField(null= True, blank= True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    reply = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = utils.get_rand_number(5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user if self.user else self.email}"





class Banner(models.Model):
    image = models.ImageField(upload_to='banners/')
    order = models.PositiveIntegerField(default=0, help_text="Order of the banner")
    active = models.BooleanField(default=True, help_text="Only active banners will be displayed")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title or 'Banner'} ({self.order})"
    
    
    
    
class Notification(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='notifications/', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    callback_url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    
    
    
class Sectionbanner(models.Model):
    BANNER_TYPES = [
        ('all', 'All Collection'),
        ('women', "Women's Collection"),
        ('men', "Men's Collection"),
    ]

    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='banners/')
    banner_type = models.CharField(max_length=10, choices=BANNER_TYPES)

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=255)  # Stores the FAQ question
    answer = models.TextField()  # Stores the answer to the question
    order = models.IntegerField(default=0)  # Used to control the order of FAQs

    class Meta:
        ordering = ['order']  # Orders FAQs by the 'order' field

    def __str__(self):
        return self.question