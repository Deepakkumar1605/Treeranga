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

        # Fetch delivery settings from the database
        delivery_settings = DeliverySettings.objects.first()
        
        # Set default values if no delivery settings are found
        delivery_charge_per_bag = delivery_settings.delivery_charge_per_bag if delivery_settings else Decimal('0.00')
        delivery_free_order_amount = delivery_settings.delivery_free_order_amount if delivery_settings else Decimal('0.00')

        # Initialize flags and values for delivery calculations
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

                # Calculate product prices and totals
                product_max_price = Decimal(product_obj.product_max_price) * quantity
                product_discount_price = Decimal(product_obj.product_discount_price) * quantity
                price_per_unit = Decimal(product_obj.product_discount_price)
                gross_cart_value += product_max_price
                our_price += product_discount_price
                total_cart_items += quantity

                # Retrieve SGST and CGST from the related Products model
                total_discounted_price = product_discount_price
                sgst_amount = product.sgst * total_discounted_price / 100
                cgst_amount = product.cgst * total_discounted_price / 100

                # Check for virtual product and delivery fee applicability
                if product.virtual_product or product.flat_delivery_fee:
                    has_virtual_or_flat_delivery_product = True
                else:
                    has_non_flat_delivery_product = True

                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'brand': product.brand,
                    'image': product.image.url if product.image else None,
                    'product_max_price': str(product_max_price.quantize(Decimal('0.01'))),
                    'product_discount_price': str(product_discount_price.quantize(Decimal('0.01'))),
                    'price_per_unit':str(price_per_unit.quantize(Decimal('0.01'))),
                    'taxable_value': str((Decimal(product_obj.taxable_value) * quantity).quantize(Decimal('0.01'))),
                    'quantity': quantity,
                    'sgst_amount': str(sgst_amount.quantize(Decimal('0.01'))),
                    'cgst_amount': str(cgst_amount.quantize(Decimal('0.01'))),
                    'total_discounted_price': str(total_discounted_price.quantize(Decimal('0.01'))),
                    'images': product_obj.image_gallery.first().images if product_obj.image_gallery.exists() else [],
                    'video': product_obj.image_gallery.first().video if product_obj.image_gallery.exists() else [],
                }

                products[key] = product_data

            except SimpleProduct.DoesNotExist:
                print(f"Error processing product {product_id}: Product does not exist")
            except Exception as e:
                print(f"Error processing product {product_id}: {e}")

        # Calculate discount and final cart value
        discount_amount = gross_cart_value - our_price
        final_cart_value = Decimal(obj.total_price)

        # Apply delivery charges based on product types and total price
        if has_virtual_or_flat_delivery_product and not has_non_flat_delivery_product:
            charges['Delivery'] = Decimal('0.00')
        elif final_cart_value < delivery_free_order_amount:
            charges['Delivery'] = delivery_charge_per_bag
        else:
            charges['Delivery'] = Decimal('0.00')

        final_cart_value += charges.get('Delivery', Decimal('0.00'))

        # Prepare the result data structure
        result = {
            'products': products,
            'total_cart_items': str(total_cart_items),  # already a str
            'gross_cart_value': "{:.2f}".format(gross_cart_value),  # convert to str
            'our_price': "{:.2f}".format(our_price),  # convert to str
            'discount_amount': "{:.2f}".format(discount_amount),  # convert to str
            'discount_percentage': "{:.1f}".format((discount_amount / gross_cart_value * 100)) if gross_cart_value > 0 else "0.0",
            'charges': {k: "{:.2f}".format(v) for k, v in charges.items()},  # already converting to str
            'final_cart_value': "{:.2f}".format(final_cart_value),  # convert to str
            'applied_coupon': obj.applied_coupon.code if obj.applied_coupon else None,
            'coupon_discount_amount': "{:.2f}".format(obj.coupon_discount_amount) if obj.coupon_discount_amount else "0.00",  # convert to str
        }

        # Convert the result to JSON-safe types
        for key, value in result.items():
            if isinstance(value, Decimal):
                result[key] = str(value)

        return result

    class Meta:
        model = Cart
        fields = ["products_data"]
