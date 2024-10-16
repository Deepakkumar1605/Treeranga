from django import forms
from .models import Variant, Attribute, VariantProduct

class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter variant name'}),
        }

class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        fields = ['variant_type', 'name', 'code']
        widgets = {
            'variant_type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter attribute name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter code'}),
        }

class ProductVariantForm(forms.ModelForm):
    product_max_price = forms.DecimalField(max_digits=10, decimal_places=2)
    product_max_price.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.01', 'required': 'required'})

    product_discount_price = forms.DecimalField(max_digits=10, decimal_places=2)
    product_discount_price.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.01', 'required': 'required'})

    stock = forms.IntegerField()
    stock.widget.attrs.update({'class': 'form-control', 'type': 'number', 'required': 'required'})

   

    class Meta:
        model = VariantProduct
        fields = ['product_max_price', 'product_discount_price', 'stock']