# Generated by Django 5.0.7 on 2024-09-04 06:03

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('slug', models.SlugField(blank=True, max_length=255, null=True, unique=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='category/')),
            ],
        ),
        migrations.CreateModel(
            name='DeliverySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_charge_per_bag', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('delivery_free_order_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Products',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.CharField(blank=True, max_length=255, null=True)),
                ('sku_no', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('brand', models.CharField(blank=True, max_length=255, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='product_image/')),
                ('product_short_description', models.TextField(blank=True, null=True)),
                ('product_long_description', models.TextField(blank=True, null=True)),
                ('trending', models.CharField(choices=[('yes', 'yes'), ('no', 'no')], default='no', max_length=255)),
                ('show_as_new', models.CharField(choices=[('yes', 'yes'), ('no', 'no')], default='no', max_length=255)),
                ('product_type', models.CharField(choices=[('simple', 'Simple Product'), ('variant', 'Variant Product')], default='simple', max_length=20)),
                ('gst_rate', models.DecimalField(choices=[(Decimal('0.00'), '0%'), (Decimal('5.00'), '5%'), (Decimal('12.00'), '12%'), (Decimal('18.00'), '18%'), (Decimal('28.00'), '28%')], decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('sgst', models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, max_digits=5)),
                ('cgst', models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, max_digits=5)),
                ('flat_delivery_fee', models.BooleanField(default=False)),
                ('virtual_product', models.BooleanField(default=False)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='product.category')),
            ],
        ),
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])),
                ('review', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='product.products')),
            ],
        ),
        migrations.CreateModel(
            name='SimpleProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_max_price', models.FloatField(blank=True, default=0.0, null=True)),
                ('product_discount_price', models.FloatField(blank=True, default=0.0, null=True)),
                ('stock', models.IntegerField(blank=True, default=1, null=True)),
                ('taxable_value', models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, max_digits=10)),
                ('is_visible', models.BooleanField(default=False)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product.products')),
            ],
        ),
        migrations.CreateModel(
            name='ImageGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('images', models.JSONField(blank=True, default=list, null=True)),
                ('video', models.JSONField(blank=True, default=list, null=True)),
                ('simple_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='image_gallery', to='product.simpleproduct')),
            ],
        ),
    ]
