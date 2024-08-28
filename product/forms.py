from django import forms
from django.forms import inlineformset_factory
from product.models import Category, DeliverySettings,Products,SimpleProduct,ImageGallery,ProductReview


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
    product_type = forms.ChoiceField(choices=Products.PRODUCT_TYPE_CHOICES, required=False)
    product_type.widget.attrs.update({'class': 'form-control', 'required': 'required'})

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
    product_short_description.widget.attrs.update({'class': 'form-control', 'rows': 5})

    product_long_description = forms.CharField(widget=forms.Textarea, required=False)
    product_long_description.widget.attrs.update({'class': 'form-control', 'rows': 5})

    trending = forms.ChoiceField(choices=Products.YESNO, required=False)
    trending.widget.attrs.update({'class': 'form-control', 'required': 'required'})

    show_as_new = forms.ChoiceField(choices=Products.YESNO, required=False)
    show_as_new.widget.attrs.update({'class': 'form-control', 'required': 'required'})

    
    gst_rate = forms.ChoiceField(choices=Products.GST_CHOICES)
    gst_rate.widget.attrs.update({'class': 'form-control', 'required': 'required'})


    class Meta:
        model = Products
        fields = [
            'product_type','category', 'sku_no', 'name', 'brand', 'image', 'product_short_description',
            'product_long_description', 'trending', 'show_as_new', 'gst_rate'
        ]

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # This is an edit form, disable the sku_no and category fields
            self.fields['sku_no'].widget.attrs['readonly'] = True
            self.fields['category'].widget.attrs['disabled'] = True
class SimpleProductForm(forms.ModelForm):
    product_max_price = forms.DecimalField(max_digits=10, decimal_places=2)
    product_max_price.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.01', 'required': 'required'})

    product_discount_price = forms.DecimalField(max_digits=10, decimal_places=2)
    product_discount_price.widget.attrs.update({'class': 'form-control', 'type': 'number', 'step': '0.01', 'required': 'required'})

    stock = forms.IntegerField()
    stock.widget.attrs.update({'class': 'form-control', 'type': 'number', 'required': 'required'})

    flat_delivery_fee = forms.BooleanField(required=False)
    flat_delivery_fee.widget.attrs.update({'class': 'form-check-input'})

    virtual_product = forms.BooleanField(required=False)
    virtual_product.widget.attrs.update({'class': 'form-check-input'})

    class Meta:
        model = SimpleProduct
        fields = ['product_max_price', 'product_discount_price', 'stock','flat_delivery_fee','virtual_product']



class DeliverySettingsForm(forms.ModelForm):
    delivery_charge_per_bag = forms.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    delivery_charge_per_bag.widget.attrs.update({
        'class': 'form-control', 
        'type': 'number', 
        'step': '0.01', 
        'required': 'required',
        'placeholder': 'Enter delivery charge per bag'
    })

    delivery_free_order_amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    delivery_free_order_amount.widget.attrs.update({
        'class': 'form-control', 
        'type': 'number', 
        'step': '0.01', 
        'required': 'required',
        'placeholder': 'Enter free delivery order amount'
    })

    class Meta:
        model = DeliverySettings
        fields = ['delivery_charge_per_bag', 'delivery_free_order_amount']


class ProductReviewForm(forms.ModelForm):
    full_name = forms.CharField(max_length=255, required=False, disabled=True, label="Full Name")
    email = forms.EmailField(required=False, disabled=True, label="Email")
 
    class Meta:
        model = ProductReview
        fields = ['rating', 'review', 'full_name', 'email']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, '★' * i) for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'review': forms.Textarea(attrs={'rows': 6,"class":"form-control"}),
        }
 
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProductReviewForm, self).__init__(*args, **kwargs)
       
        if user:
            self.fields['full_name'].initial = user.full_name
            self.fields['email'].initial = user.email
       
        self.fields['rating'].widget.attrs['class'] += ' star-rating'