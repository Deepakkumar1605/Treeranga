# Generated by Django 5.0.7 on 2024-08-21 14:59

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0012_alter_simpleproduct_gst_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='simpleproduct',
            name='cgst',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, max_digits=5),
        ),
        migrations.AddField(
            model_name='simpleproduct',
            name='sgst',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, max_digits=5),
        ),
    ]
