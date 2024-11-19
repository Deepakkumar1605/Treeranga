from django import forms
from app_common.models import ContactMessage,Banner, Notification, Sectionbanner
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class ContactMessageForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={ 'class':'form-control','placeholder': 'Name',}),
       
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={ 'class':'form-control', 'placeholder': 'Email'}),
        required=True,
       
    )
    contact = forms.CharField(
        max_length=10,
        
        validators=[RegexValidator(regex='^[9876]\d{9}$')],
        widget=forms.TextInput(attrs={ 'class':'form-control','placeholder': 'Phone Number'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={ 'class':'form-control','placeholder': 'Comment here!'}),
        required=True,
      
    )


class ReplyForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['reply']
        widgets = {
            'reply': forms.Textarea(attrs={'rows': 8,'class':'form-control', 'placeholder': 'Type your Reply here...'}),
        }


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = '__all__'
        
        
        
class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'description', 'image', 'callback_url', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notification Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notification Description'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'callback_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Callback URL'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        
class SectionBannerForm(forms.ModelForm):
    class Meta:
        model = Sectionbanner
        fields = ['title', 'image', 'banner_type']