from django.conf import settings
from django.shortcuts import render, redirect, HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.contrib import messages
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from blog.models import Blogs

from uuid import uuid4
import datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from io import StringIO
from django.core.mail import send_mail
import json
from django.contrib.auth.decorators import login_required
from app_common.models import (
    User,
    ContactMessage,
)



app = "blog/"



class BlogView(View):
    template_name = app + 'user/user_blog_list.html'

    def get(self, request):
        return render(request, self.template_name)
    

class BlogCategory(View):
    template_name = app + 'user/user_blog_list.html'

    def get(self, request):

        blogs = Blogs.objects.all()
        # highlighted_blogs = Blogs.objects.filter(is_highlight=True)
        context = {
            'blogs': blogs,
            # 'highlighted_blogs': highlighted_blogs,
        }
        return render(request, self.template_name, context)

class BlogDetails(View):
    template_name = app + 'user/user_blog_single.html'

    def get(self, request, slug):
        blogdetail = get_object_or_404(Blogs, slug=slug)
        context = {
            'blogdetail': blogdetail,
        }
        return render(request, self.template_name, context)
    
