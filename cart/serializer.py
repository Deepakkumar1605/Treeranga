from decimal import Decimal
from rest_framework import serializers
from product.models import DeliverySettings, SimpleProduct
from product_variations.models import VariantProduct
from .models import Cart

class CartSerializer(serializers.ModelSerializer):
    products_data = serializers.SerializerMethodField()

    def get_products_data(self, obj):
        total_cart_items = 0
        gross_cart_value = Decimal('0.00')
        our_price = Decimal('0.00')
        charges = {}
        products = {}

        # Fetch delivery settings
        delivery_settings = DeliverySettings.objects.first()
        delivery_charge_per_bag = delivery_settings.delivery_charge_per_bag if delivery_settings else Decimal('0.00')
        delivery_free_order_amount = delivery_settings.delivery_free_order_amount if delivery_settings else Decimal('0.00')

        has_virtual_or_flat_delivery_product = False
        has_non_flat_delivery_product = False

        for key, value in obj.products.items():
            product_key_parts = key.split('_')
            product_id = product_key_parts[0]

            try:
                if value['info']['variant'] == "yes":
                    product_obj = VariantProduct.objects.get(id=product_id)
                else:
                    product_obj = SimpleProduct.objects.get(id=product_id)

                product = product_obj.product
                quantity = Decimal(value['quantity'])

                product_max_price = Decimal(product_obj.product_max_price) * quantity
                product_discount_price = Decimal(product_obj.product_discount_price) * quantity
                price_per_unit = Decimal(product_obj.product_discount_price)
                gross_cart_value += product_max_price
                our_price += product_discount_price
                total_cart_items += quantity

                if product.virtual_product or product.flat_delivery_fee:
                    has_virtual_or_flat_delivery_product = True
                else:
                    has_non_flat_delivery_product = True

            except Exception as e:
                print(f"Error processing product {product_id}: {e}")

        discount_amount = gross_cart_value - our_price

        # Apply delivery charges
        if has_virtual_or_flat_delivery_product and not has_non_flat_delivery_product:
            charges['Delivery'] = Decimal('0.00')
        elif our_price < delivery_free_order_amount:
            charges['Delivery'] = delivery_charge_per_bag
        else:
            charges['Delivery'] = Decimal('0.00')

        # Apply coupon discount only once
        coupon_discount = Decimal('0.00')
        if obj.applied_coupon:
            coupon_discount = Decimal(obj.applied_coupon.discount_value)

        final_cart_value = our_price - coupon_discount + charges.get('Delivery', Decimal('0.00'))

        result = {
            'products': products,
            'total_cart_items': str(total_cart_items),
            'gross_cart_value': "{:.2f}".format(gross_cart_value),
            'our_price': "{:.2f}".format(our_price),
            'discount_amount': "{:.2f}".format(discount_amount),
            'charges': {k: "{:.2f}".format(v) for k, v in charges.items()},
            'final_cart_value': "{:.2f}".format(final_cart_value),
            'applied_coupon': obj.applied_coupon.code if obj.applied_coupon else None,
            'coupon_discount_amount': "{:.2f}".format(coupon_discount) if obj.applied_coupon else "0.00",
        }

        return result

    class Meta:
        model = Cart
        fields = ["products_data"]

