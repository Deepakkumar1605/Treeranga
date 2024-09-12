from rest_framework import serializers
from .models import Blogs

class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blogs
        fields = ['id', 'slug', 'title', 'author', 'date', 'content', 'image']
