from django import forms
from django.contrib.auth.forms import PasswordChangeForm,PasswordResetForm,SetPasswordForm
from users.models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re


class SignUpForm(forms.Form):

    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control','placeholder':'Enter Your Full Name'}))
    email = forms.EmailField(max_length=254,
                             widget=forms.EmailInput(attrs={'class': 'form-control','placeholder':'Enter Valid Email Address'}))
    contact = forms.CharField(max_length=10,
        validators=[RegexValidator(regex='^[9876]\d{9}$')],widget=forms.TextInput(attrs={'class': 'form-control','Placeholder':'Enter Mobile Number'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder':'Enter Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder':'Enter Confirm Password'}))



    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email address already exists")
        return email

    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        if User.objects.filter(contact=contact).exists():
            raise forms.ValidationError("Contact number already exists")
        return contact


    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 6 :
            raise ValidationError('Password length must be 6 characters.')

        if not re.search(r'[A-Za-z]', password):
            raise ValidationError('Password must contain at least one alphabet.')

        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one number.')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character.')

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data

class LoginForm(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control','placeholder':'Enter Valid Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder':'Enter Password'}))
    
class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control','placeholder':'Enter Valid Email Address'}))
    
 
class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
   
 


class UpdateProfileForm(forms.Form):
    
    email = forms.EmailField(max_length=255)
    email.widget.attrs.update({'class': 'form-control','type':'text','placeholder':'Enter Email',"required":"required"})

    full_name = forms.CharField(max_length=255)
    full_name.widget.attrs.update({'class': 'form-control','type':'text','placeholder':'Enter Full Name',"required":"required"})

    contact = forms.CharField(max_length=10,help_text='Required. Enter Mobile Number',
        validators=[RegexValidator(regex='^[9876]\d{9}$')],widget=forms.TextInput(attrs={'class': 'form-control'}))

    profile_pic = forms.FileField(label='Select an image file', required=False)
    profile_pic.widget.attrs.update({'class': 'form-control', 'type': 'file'})




class AddressForm(forms.Form):
    Address1 = forms.CharField(max_length=255)
    Address1.widget.attrs.update({'class': 'form-control','type':'text',"required":"required"})

    Address2 = forms.CharField(max_length=255)
    Address2.widget.attrs.update({'class': 'form-control','type':'text',"required":"required"})

    mobile_no = forms.CharField(max_length=10,help_text='Required. Enter Mobile Number',
        validators=[RegexValidator(regex='^[9876]\d{9}$')],widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    country = forms.CharField(max_length=255)
    country.widget.attrs.update({'class': 'form-control','type':'text',"required":"required"})

    state = forms.CharField(max_length=255)
    state.widget.attrs.update({'class': 'form-control','type':'text',"required":"required"})

    city = forms.CharField(max_length=255)
    city.widget.attrs.update({'class': 'form-control','type':'text',"required":"required"})
    
    pincode = forms.IntegerField()
    pincode.widget.attrs.update({'class': 'form-control','type':'text','placeholder':'Enter Pincode',"required":"required"})



class EditUserForm(forms.Form):
    model =User
    email = forms.EmailField(label="Email",max_length=50,widget=forms.EmailInput(attrs={"class":"form-control"}))
    full_name = forms.CharField(label="Full Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    contact = forms.IntegerField(label="Contact",widget=forms.NumberInput(attrs={"class":"form-control"}))



class AddUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'full_name', 'contact', 'password']  # Include necessary fields

    # Optionally, you can add custom validation or widgets
    password = forms.CharField(widget=forms.PasswordInput)