# Generated by Django 5.0.7 on 2024-08-22 06:06

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0014_remove_simpleproduct_cgst_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='cgst_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, max_digits=10),
        ),
        migrations.AddField(
            model_name='products',
            name='gst_price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='products',
            name='sgst_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, max_digits=10),
        ),
    ]
