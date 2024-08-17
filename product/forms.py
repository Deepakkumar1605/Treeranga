from django import forms
from django.forms import inlineformset_factory
from product.models import Category,Products,SimpleProduct,ImageGallery


class CategoryEntryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = [
            'title',
            'image'

        ]

    title = forms.CharField(max_length=255)
    title.widget.attrs.update({'class': 'form-control','type':'text',"required":"required"})

    
    image = forms.ImageField(label='image', required=True)
    image.widget.attrs.update({'class': 'form-control','type':'file'})

    


class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    category.widget.attrs.update({'class': 'form-control', 'required': 'required'})

    sku_no = forms.CharField(max_length=255)
    sku_no.widget.attrs.update({'class': 'form-control', 'type': 'text', 'required': 'required'})

    name = forms.CharField(max_length=255)
    name.widget.attrs.update({'class': 'form-control', 'type': 'text', 'required': 'required'})

    brand = forms.CharField(max_length=255, required=False)
    brand.widget.attrs.update({'class': 'form-control', 'type': 'text'})

    image = forms.ImageField(label='Image', required=False)
    image.widget.attrs.update({'class': 'form-control', 'type': 'file'})

    product_short_description = forms.CharField(widget=forms.Textarea, required=False)
    product_short_description.widget.attrs.update({'class': 'form-control', 'rows': 3})

    product_long_description = forms.CharField(widget=forms.Textarea, required=False)
    product_long_description.widget.attrs.update({'class': 'form-control', 'rows': 5})

    trending = forms.ChoiceField(choices=Products.YESNO, required=False)
    trending.widget.attrs.update({'class': 'form-control', 'required': 'required'})

    show_as_new = forms.ChoiceField(choices=Products.YESNO, required=False)
    show_as_new.widget.attrs.update({'class': 'form-control', 'required': 'required'})

    product_type = forms.ChoiceField(choices=Products.PRODUCT_TYPE_CHOICES, required=False)
    product_type.widget.attrs.update({'class': 'form-control', 'required': 'required'})

    class Meta:
        model = Products
        fields = [
            'category', 'sku_no', 'name', 'brand', 'image', 'product_short_description',
            'product_long_description', 'trending', 'show_as_new', 'product_type'
        ]
class SimpleProductForm(forms.ModelForm):
    product_max_price = forms.DecimalField(max_digits=10, decimal_places=2)
    product_max_price.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.01', 'required': 'required'})

    product_discount_price = forms.DecimalField(max_digits=10, decimal_places=2)
    product_discount_price.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.01', 'required': 'required'})

    stock = forms.IntegerField()
    stock.widget.attrs.update({'class': 'form-control', 'type': 'number', 'required': 'required'})

    sgst_rate = forms.DecimalField(max_digits=5, decimal_places=3)
    sgst_rate.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.001', 'required': 'required'})

    cgst_rate = forms.DecimalField(max_digits=5, decimal_places=3)
    cgst_rate.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.001', 'required': 'required'})

    

    class Meta:
        model = SimpleProduct
        fields = ['product_max_price', 'product_discount_price', 'stock','sgst_rate', 'cgst_rate']



