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


app = 'coupons/'


class Getcoupons(View):
    template = app + "users/all_coupons_page.html"  

    def get(self, request):
        # try:
            if request.user.is_superuser:
                return redirect('users:admin_dashboard')  # Redirect if the user is an admin

            # Get all active coupons that are valid based on the 'is_valid' method
            all_coupons = Coupon.objects.filter(is_active=True)
            valid_coupons = [coupon for coupon in all_coupons if coupon.is_valid()]

            context = {
                "all_coupons": valid_coupons,
            }
            return render(request, self.template, context)

        # except Exception as e:
        #     error_message = f"An unexpected error occurred: {str(e)}"
        #     return render_error_page(request, error_message, status_code=400)