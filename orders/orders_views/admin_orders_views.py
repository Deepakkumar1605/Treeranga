from django.conf import settings
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from helpers import utils, api_permission
from django.forms.models import model_to_dict
import json
from helpers import utils
from orders.models import Order
from decimal import Decimal
from product.models import Products
from orders.serializer import OrderSerializer
from orders.forms import OrderUpdateForm
from orders.tasks import update_order_status
import logging

app = "orders/admin/"

# ================================================== patient management ==========================================

@method_decorator(utils.super_admin_only, name='dispatch')
class OrderList(View):
    model = Order
    template = app + "order_list.html"

    def get(self,request):

        order_list = self.model.objects.all().order_by('-id')
        paginated_data = utils.paginate(request, order_list, 50)
        order_status_options = Order.ORDER_STATUS
        print(paginated_data)
        context = {
            "order_list":order_list,
            "order_status_options":order_status_options,
        }
        return render(request, self.template,context)

@method_decorator(utils.super_admin_only, name='dispatch')
class OrderStatusSearch(View):
    model = Order
    template = app + "order_list.html"

    def get(self,request):
        filter_by = request.GET.get('filter_by')
        order_list = self.model.objects.filter(order_status = filter_by)
        paginated_data = utils.paginate(request, order_list, 50)
        order_status_options = Order.ORDER_STATUS
        
        context = {
            "order_list":paginated_data,
            "order_status_options":order_status_options,
        }
        return render(request, self.template,context)


@method_decorator(utils.super_admin_only, name='dispatch')
class OrderSearch(View):
    model = Order
    template = app + "order_list.html"

    def get(self,request):
        query = request.GET.get('query')
        order_list = self.model.objects.filter(uid__icontains = query)
        order_status_options = Order.ORDER_STATUS

        context = {
            "order_list":order_list,
            "order_status_options":order_status_options,
        }
        return render(request, self.template,context)


@method_decorator(utils.super_admin_only, name='dispatch')
class AdminOrderDetail(View):
    model = Order
    form_class = OrderUpdateForm
    template = app + "admin_order_detail.html"

    def get(self, request, order_uid):
        # Fetch the order using the UID
        print(order_uid)
        order = get_object_or_404(Order, uid=order_uid)
        form = self.form_class(instance=order, initial={'order_status': order.order_status})
        
        product_list = []
        product_quantity = []
        total_quantity = 0
        grand_total = 0

        # Extract the grand total from the order's metadata
        try:
            grand_total = order.order_meta_data.get('final_cart_value', 0)
        except KeyError:
            grand_total = order.order_meta_data.get('final_value', 0)

        # Iterate over the products in the order
        for product_id, details in order.products.items():
            product = get_object_or_404(Products, name=details['info']['name'])
            product_list.append(product)
            product_quantity.append(details['quantity'])
            total_quantity += int(details['quantity'])

        # Zip together the products and their quantities
        zipproduct = zip(product_list, product_quantity)

        context = {
            'order': order,
            'grand_total': grand_total,
            'zipproduct': zipproduct,
            'total_quantity': total_quantity,
            "MEDIA_URL": settings.MEDIA_URL,
            "form": form,
            "order_address": order.address
        }
        return render(request, self.template, context)
    
    def post(self, request, order_uid):
        order = self.model.objects.get(uid=order_uid)
        form = self.form_class(request.POST, instance=order)

        if form.is_valid():
            obj = form.save()
            # update_order_status.delay(obj.user.email, OrderSerializer(obj).data)
            messages.success(request, 'Order Status is updated....')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        return redirect('orders:admin_order_details', order_uid=order_uid)



@method_decorator(utils.super_admin_only, name='dispatch')
class DownloadInvoice(View):
    model = Order
    template = 'orders/admin/invoice.html'
 
    def get(self, request, order_uid):
        order = self.model.objects.get(uid=order_uid)
        data = OrderSerializer(order).data
        
        
        products = []
        quantities = []
        price_per_unit = []
        total_prices = []

        total_cgst = Decimal('0.00')
        total_sgst = Decimal('0.00')

        # Loop through each product to extract and calculate required information
        for product_id, p_overview in data['order_meta_data']['products'].items():
            products.append(p_overview['name'])
            quantities.append(p_overview['quantity'])
            price_per_unit.append(p_overview['product_discount_price'])
            total_prices.append(p_overview['total_price'])
 
            # Calculate the total CGST and SGST
            total_cgst += Decimal(p_overview.get('cgst_amount', '0.00'))
            total_sgst += Decimal(p_overview.get('sgst_amount', '0.00'))

        prod_quant = zip(products, quantities, price_per_unit, total_prices)
 
        try:
            final_total = data['order_meta_data']['final_cart_value']
        except KeyError:
        
            final_total = data['order_meta_data']['final_value']
 
        # Prepare context data for rendering the invoice
        context = {
            'order': data,
            'address': data['address'],
            'user': order.user,
            'productandquantity': prod_quant,
            'delivery_charge': data['order_meta_data']['charges']['Delivery'],
            'cgst_amount': "{:.2f}".format(total_cgst),
            'sgst_amount': "{:.2f}".format(total_sgst),
            'gross_amt': data['order_meta_data']['our_price'],
            'discount': data['order_meta_data'].get('discount_amount', '0.00'),
            'final_total': final_total
        }
 
        # Render the template with the provided context
        return render(request, self.template, context)