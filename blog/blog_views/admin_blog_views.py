from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.conf import settings
#import requests
from django.http import JsonResponse
import json
from blog.forms import BlogForm
from blog.models import Blogs
from helpers import utils
from django.forms.models import model_to_dict
import os
from django.urls import reverse

# for api
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# -------------------------------------------- custom import



app = "blog/"

# ================================================== Room management ==========================================
    

@method_decorator(utils.super_admin_only, name='dispatch')
class BlogList(View):
    model = Blogs
    template = app + "admin/blog_list.html"

    def get(self, request):
        blog_list = self.model.objects.all().order_by('-id')
        print(blog_list)
        
        paginated_data = utils.paginate(
            request, blog_list, 50  
        )
        context = {
            "blog_list": blog_list,
            "data_list": paginated_data
        }
        return render(request, self.template, context)


@method_decorator(utils.super_admin_only, name='dispatch')
class BlogSearch(View):
    model = Blogs
    form_class = BlogForm
    template = app + "admin/blog_list.html"

    def post(self,request):
        filter_by = request.POST.get("filter_by")
        query = request.POST.get("query")
        product_list = []
        if filter_by == "id":
            blog_list = self.model.objects.filter(id = query)
        else:
            blog_list = self.model.objects.filter(title__icontains = query)

        paginated_data = utils.paginate(
            request, blog_list, 50
        )
        context = {
            "form": self.form_class,
            "blog_list":blog_list,
            "data_list":paginated_data
        }
        return render(request, self.template, context)

    

class BlogFilter(View):
    model = Blogs
    template = app + "admin/blog_list.html"

    def get(self,request):
        filter_by = request.GET.get("filter_by")

        if filter_by == "trending":
            blog_list = self.model.objects.filter(trending="yes").order_by('-id')

        elif filter_by == "show_as_new":
            blog_list = self.model.objects.filter(show_as_new="yes").order_by('-id')

        elif filter_by == "display_as_bestseller":
            blog_list = self.model.objects.filter(display_as_bestseller="yes").order_by('-id')

        elif filter_by == "hide":
            blog_list = self.model.objects.filter(hide="yes").order_by('-id')        

        else:
            blog_list = self.model.objects.filter().order_by('-id')

        paginated_data = utils.paginate(
            request, blog_list, 50
        )

        context = {
            "blog_list":blog_list,
            "data_list":paginated_data
        }
        return render(request, self.template, context)
    

@method_decorator(utils.super_admin_only, name='dispatch')
class BlogAdd(View):
    model = Blogs
    form_class = BlogForm
    template = app + "admin/blog_add.html"

    def get(self,request):
        blog_list = self.model.objects.all().order_by('-id')
        context = {
            "blog_list" : blog_list,
            "form": self.form_class,
        }
        return render(request, self.template, context)
    
    def post(self, request):

        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"Blog is added successfully.....")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        return redirect("blog:blog_list")



@method_decorator(utils.super_admin_only, name='dispatch')
class BlogUpdate(View):
    model = Blogs
    form_class = BlogForm
    template = app + "admin/blog_update.html"

    def get(self,request, blog_id):
        blog = self.model.objects.get(id = blog_id)
 
        context = {
            "blog" : blog,
            "form": self.form_class(instance=blog),
        }
        return render(request, self.template, context)
    
    def post(self,request, blog_id):

        blog = self.model.objects.get(id = blog_id)
        form = self.form_class(request.POST, request.FILES, instance=blog)

        if form.is_valid():
            form.save()
            messages.success(request, f"Blog ({blog_id}) is updated successfully.....")
            return redirect(reverse('blog:blog_list'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        return redirect("blog:blog_update", blog_id = blog_id)


@method_decorator(utils.super_admin_only, name='dispatch')
class BlogDelete(View):
    model = Blogs

    def get(self,request, blog_id):
        blog = self.model.objects.get(id = blog_id)

        if blog.image:
            image_path = blog.image.path
            os.remove(image_path)

        blog.delete()
        messages.info(request, 'Blog is deleted succesfully......')

        return redirect("blog:blog_list")
    