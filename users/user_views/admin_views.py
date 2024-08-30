from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from helpers import utils
from users import models,forms
from orders.models import Order
app = "users/admin/"

# admin dashboard and manage users list

@method_decorator(utils.super_admin_only, name='dispatch')
class AdminDashboard(View):
    template = app + "index.html"  # Update the template path if necessary

    def get(self, request):
        return render(request, self.template)


class UserList(View):
    model = models.User
    template = app + "user_list.html"

    def get(self,request):
        user_obj = self.model.objects.filter(is_superuser=False).order_by("id")
        return render(request,self.template,{"user_obj":user_obj})


class UserDetailView(View):
    model = models.User
    template = app + "user_profile.html"
    def get(self, request, user_id):
        user_obj = get_object_or_404(self.model, id=user_id)
        orders = Order.objects.filter(user=user_obj).order_by('-date')  # Adjust the field name and ordering as needed

        context = {
            "user_obj": user_obj,
            "orders": orders
        }
        return render(request, self.template, context)

