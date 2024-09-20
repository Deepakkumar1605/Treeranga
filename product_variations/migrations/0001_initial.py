# Generated by Django 5.0.7 on 2024-09-19 11:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('code', models.CharField(blank=True, max_length=100, null=True)),
                ('variant_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product_variations.variant')),
            ],
        ),
        migrations.CreateModel(
            name='VariantProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant_combination', models.JSONField(blank=True, null=True)),
                ('product_max_price', models.FloatField(blank=True, default=0.0, null=True)),
                ('product_discount_price', models.FloatField(blank=True, default=0.0, null=True)),
                ('stock', models.IntegerField(blank=True, default=1, null=True)),
                ('taxable_value', models.DecimalField(decimal_places=2, default=0.0, editable=False, max_digits=10)),
                ('is_visible', models.BooleanField(default=False)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product.products')),
            ],
        ),
        migrations.CreateModel(
            name='VariantImageGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('images', models.JSONField(blank=True, default=list, null=True)),
                ('video', models.JSONField(blank=True, default=list, null=True)),
                ('variant_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='image_gallery', to='product_variations.variantproduct')),
            ],
        ),
    ]
