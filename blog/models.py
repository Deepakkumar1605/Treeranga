from django.db import models
from ckeditor.fields import RichTextField
from helpers import utils
from django.template.defaultfilters import slugify

class Blogs(models.Model):
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    date = models.DateField()
    content = RichTextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    # is_highlight = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
            if not self.slug:
                self.slug = slugify(self.title)
            super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

 
