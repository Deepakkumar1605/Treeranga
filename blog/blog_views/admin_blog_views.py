from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
#import requests
from django.http import JsonResponse
import json
from app_common.error import render_error_page
from blog.forms import BlogForm
from blog.models import Blogs
from helpers import utils
from django.forms.models import model_to_dict
import os
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
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
        try:
            blog_list = self.model.objects.all().order_by('-id')

            # Pagination
            paginator = Paginator(blog_list, 10)  # Show 10 blogs per page
            page = request.GET.get('page')
            try:
                paginated_data = paginator.page(page)
            except PageNotAnInteger:
                paginated_data = paginator.page(1)
            except EmptyPage:
                paginated_data = paginator.page(paginator.num_pages)

            context = {
                "blog_list": paginated_data,
                "paginator": paginator
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


@method_decorator(utils.super_admin_only, name='dispatch')
class BlogSearch(View):
    model = Blogs
    form_class = BlogForm
    template = app + "admin/blog_list.html"

    def post(self, request):
        try:
            filter_by = request.POST.get("filter_by")
            query = request.POST.get("query")
            blog_list = []

            if filter_by == "id":
                blog_list = self.model.objects.filter(id=query)
            else:
                blog_list = self.model.objects.filter(title__icontains=query)

            paginated_data = utils.paginate(request, blog_list, 50)
            context = {
                "form": self.form_class,
                "blog_list": blog_list,
                "data_list": paginated_data
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class BlogFilter(View):
    model = Blogs
    template = app + "admin/blog_list.html"

    def get(self, request):
        try:
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

            paginated_data = utils.paginate(request, blog_list, 50)
            context = {
                "blog_list": blog_list,
                "data_list": paginated_data
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


@method_decorator(utils.super_admin_only, name='dispatch')
class BlogAdd(View):
    model = Blogs
    form_class = BlogForm
    template = app + "admin/blog_add.html"

    def get(self, request):
        try:
            blog_list = self.model.objects.all().order_by('-id')
            context = {
                "blog_list": blog_list,
                "form": self.form_class,
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request):
        try:
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Blog added successfully.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')

            return redirect("blog:blog_list")
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


@method_decorator(utils.super_admin_only, name='dispatch')
class BlogUpdate(View):
    model = Blogs
    form_class = BlogForm
    template = app + "admin/blog_update.html"

    def get(self, request, blog_id):
        try:
            blog = self.model.objects.get(id=blog_id)
            context = {
                "blog": blog,
                "form": self.form_class(instance=blog),
            }
            return render(request, self.template, context)
        except ObjectDoesNotExist:
            error_message = "Blog not found."
            return render_error_page(request, error_message, status_code=404)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request, blog_id):
        try:
            blog = self.model.objects.get(id=blog_id)
            form = self.form_class(request.POST, request.FILES, instance=blog)

            if form.is_valid():
                form.save()
                messages.success(request, f"Blog ({blog_id}) updated successfully.")
                return redirect(reverse('blog:blog_list'))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')

            return redirect("blog:blog_update", blog_id=blog_id)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


@method_decorator(utils.super_admin_only, name='dispatch')
class BlogDelete(View):
    model = Blogs

    def get(self, request, blog_id):
        try:
            blog = self.model.objects.get(id=blog_id)

            if blog.image:
                image_path = blog.image.path
                os.remove(image_path)

            blog.delete()
            messages.info(request, 'Blog deleted successfully.')
            return redirect("blog:blog_list")
        except ObjectDoesNotExist:
            error_message = "Blog not found."
            return render_error_page(request, error_message, status_code=404)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)