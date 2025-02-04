from decimal import Decimal
from django.shortcuts import render, redirect, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404
from app_common.error import render_error_page
from orders.serializer import OrderSerializer
from django.views import View
from orders.models import Order
from product.models import Products

from payment.payment_views.delhivery_api import track_delhivery_order


app = "orders/user/"

class UserOrder(View):
    template = app + "user_order.html"

    def get(self, request):
        try:
            user = request.user
            orders = Order.objects.filter(user=user).order_by("-id")
            return render(request, self.template, {'orders': orders})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class OrderDetail(View):
    template = app + 'order_details.html'  

    def get(self, request, order_uid):
        try:
            order = get_object_or_404(Order, uid=order_uid)
            
            # Fetch order metadata and use order.uid as ref_id
            ref_id = str(order.uid)  # Using the order UID for tracking
            # Call the Delhivery tracking function with ref_id
            tracking_response = track_delhivery_order(ref_id=ref_id)
            # Get the tracking data from the response
            tracking_data = tracking_response.get('data', []) if tracking_response.get('success') else []

            product_list = []
            product_quantity = []
            total_quantity = 0
            grand_total = 0.0
            total_cgst = 0.0
            total_sgst = 0.0

            # Extract values from the order's metadata
            order_meta_data = order.order_meta_data
            grand_total = float(order_meta_data.get('final_cart_value', '0.00'))
            discount_amount = float(order_meta_data.get('discount_amount', '0.00'))
            gross_cart_value = float(order_meta_data.get('gross_cart_value', '0.00'))
            total_cart_items = int(order_meta_data.get('total_cart_items', 0))
            delivery_charge = float(order_meta_data.get('charges', {}).get('Delivery', '0.00'))
            applied_coupon = order_meta_data.get('applied_coupon',None)
            coupon_discount_amount = order_meta_data.get('coupon_discount_amount','0.00')

            products = []
            quantities = []
            price_per_unit = []
            total_prices = []

            # Calculate total CGST and SGST
            for product_id, details in order_meta_data.get('products', {}).items():
                total_cgst += float(details.get('cgst_amount', '0.00'))
                total_sgst += float(details.get('sgst_amount', '0.00'))
                
                # Fetch product and calculate price details
                product = get_object_or_404(Products, id=details['id'])
                products.append(product)
                quantities.append(details['quantity'])
                price_per_unit.append(details['price_per_unit'])
                total_prices.append(float(details['total_discounted_price']))
                total_quantity += int(details['quantity'])

            zipproduct = zip(products, quantities, price_per_unit, total_prices)

            context = {
                'order': order,
                'grand_total': grand_total,
                'zipproduct': zipproduct,
                'total_quantity': total_quantity,
                'discount_amount': discount_amount,
                'gross_cart_value': gross_cart_value,
                'total_cart_items': total_cart_items,
                'applied_coupon':applied_coupon,
                'coupon_discount_amount':coupon_discount_amount,
                'cgst_amount': total_cgst,
                'sgst_amount': total_sgst,
                'delivery_charge': delivery_charge,
                'payment_method': order.payment_method,
                "MEDIA_URL": settings.MEDIA_URL,
                'tracking_data': tracking_data  # Add tracking data to context
            }
            return render(request, self.template, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
        
        



class UserDownloadInvoice(View):
    model = Order
    template = 'orders/admin/invoice.html'

    def get(self, request, order_uid):
        try:
            order = self.model.objects.get(uid=order_uid)
            data = OrderSerializer(order).data
            
            products = []
            quantities = []
            price_per_unit = []
            total_prices = []

            total_cgst = Decimal('0.00')
            total_sgst = Decimal('0.00')
            applied_coupon = order.order_meta_data.get('applied_coupon',None)
            coupon_discount_amount = order.order_meta_data.get('coupon_discount_amount','0.00')
            # Loop through each product to extract and calculate required information
            for product_id, p_overview in data['order_meta_data']['products'].items():
                products.append(p_overview['name'])
                quantities.append(p_overview['quantity'])
                price_per_unit.append(p_overview['price_per_unit'])
                total_prices.append(p_overview['total_discounted_price'])
    
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
                'final_total': final_total,
                'applied_coupon':applied_coupon,
                'coupon_discount_amount':coupon_discount_amount,
            }

            # Render the template with the provided context
            return render(request, self.template, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
