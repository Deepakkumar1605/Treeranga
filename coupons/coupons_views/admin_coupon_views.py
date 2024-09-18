from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.conf import settings
from app_common.error import render_error_page
from coupons.forms import CouponForm
from coupons.models import Coupon
from helpers import utils
from os.path import join
from django.core.files.storage import default_storage

app = 'coupons/'

@method_decorator(utils.super_admin_only, name='dispatch')
class CouponList(View):
    model = Coupon
    template = app + "admin/coupon_list.html"

    def get(self, request):
        try:
            coupon_list = self.model.objects.all().order_by('-id')
            context = {
                "coupon_list": coupon_list,
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

@method_decorator(utils.super_admin_only, name='dispatch')
class CouponAdd(View):
    model = Coupon
    form_class = CouponForm
    template = app + "admin/coupon_add.html"

    def get(self, request):
        try:
            coupon_list = self.model.objects.all().order_by('-id')
            context = {
                "coupon_list": coupon_list,
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
                messages.success(request, "Coupon added successfully.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            return redirect("coupons:coupon_list")
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

@method_decorator(utils.super_admin_only, name='dispatch')
class CouponUpdate(View):
    model = Coupon
    form_class = CouponForm
    template = app + "admin/coupon_update.html"

    def get(self, request, coupon_id):
        try:
            coupon = get_object_or_404(self.model, id=coupon_id)
            form = self.form_class(instance=coupon)
            return render(request, self.template, {'form': form})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request, coupon_id):
        try:
            coupon = get_object_or_404(self.model, id=coupon_id)
            form = self.form_class(request.POST, request.FILES, instance=coupon)
            if form.is_valid():
                form.save()
                messages.success(request, f"{coupon.code} updated successfully.")
                return redirect("coupons:coupon_list")
            else:
                messages.error(request, "Form is not valid. Please check the errors.")
                return render(request, self.template, {'form': form})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

@method_decorator(utils.super_admin_only, name='dispatch')
class CouponDelete(View):
    model = Coupon
    template = app + "admin/coupon_delete.html"

    def get(self, request, coupon_id):
        try:
            coupon = self.model.objects.get(id=coupon_id).delete()
            messages.info(request, "Coupon deleted successfully.")
            return redirect("coupons:coupon_list")
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
