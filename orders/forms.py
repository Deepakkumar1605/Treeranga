from django import forms
from orders.models import Order

class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_status',
        ]
    
    order_status = forms.ChoiceField(choices = Order.ORDER_STATUS)
    order_status.widget.attrs.update({'class': 'form-control','type':'text',"required":"required"})