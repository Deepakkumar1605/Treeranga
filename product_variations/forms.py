from django import forms

from product.models import Products, SimpleProduct
from .models import ProductAttribute, ProductVariation

class ProductVariationForm(forms.ModelForm):
    parent_product = forms.ModelChoiceField(
        queryset=Products.objects.all(),
        required=True,
        label='Parent Product'
    )
    parent_product.widget.attrs.update({'class': 'form-control', 'required': 'required'})

    variation_attributes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True,
        label='Variation Attributes'
    )
    variation_attributes.widget.attrs.update({'class': 'form-control', 'required': 'required', 'placeholder': 'Enter attributes as JSON (e.g., {"size": "small", "color": "red"})'})

    product_max_price = forms.FloatField(
        required=False,
        label='Max Price'
    )
    product_max_price.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.01'})

    product_discount_price = forms.FloatField(
        required=False,
        label='Discount Price'
    )
    product_discount_price.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.01'})

    stock = forms.IntegerField(
        required=True,
        label='Stock Quantity'
    )
    stock.widget.attrs.update({'class': 'form-control', 'type': 'number'})

    class Meta:
        model = ProductVariation
        fields = ['parent_product', 'variation_attributes', 'product_max_price', 'product_discount_price', 'stock']

class ProductAttributeForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        required=True,
        label='Attribute Name'
    )
    name.widget.attrs.update({'class': 'form-control', 'type': 'text', 'required': 'required'})

    value = forms.CharField(
        max_length=255,
        required=True,
        label='Attribute Value'
    )
    value.widget.attrs.update({'class': 'form-control', 'type': 'text', 'required': 'required'})

    product = forms.ModelChoiceField(
        queryset=Products.objects.all(),
        required=True,
        label='Product'
    )
    product.widget.attrs.update({'class': 'form-control', 'required': 'required'})

    class Meta:
        model = ProductAttribute
        fields = ['name', 'value', 'product']