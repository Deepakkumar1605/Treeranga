from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from app_common import forms
from app_common.models import ContactMessage
from users.forms import LoginForm
from app_common.models import ContactMessage
from app_common.forms import ContactMessageForm
from product.models import Category,Products,SimpleProduct,ImageGallery
from cart.models import Cart
from django.conf import settings
from django.db.models import Prefetch


app = "app_common/"


# static pages 


class HomeView(View):
    template = app + "landing_page.html"

    def get(self, request):
        categories = Category.objects.all()
        trending_products = Products.objects.filter(trending="yes").order_by('-id')[:6]
        new_products = Products.objects.filter(show_as_new="yes").order_by('-id')[:6]
        # cart = Cart.objects.filter(user=request.user).first()
        # if cart:
        # # Assuming 'products' is stored as a list of dictionaries in JSON
        #     cart_products = cart.products
        #     cart_count = sum(item['quantity'] for item in cart_products.values()) if cart_products else 0
        # else:
        #     cart_count = 0
        
        context = {
            'categories': categories,
            'trending_products': trending_products,
            'new_products': new_products,
            # 'cart_count': cart_count,
            'MEDIA_URL': settings.MEDIA_URL,
        }
        return render(request, self.template, context)


class AboutUs(View):
    template = app + "about_us.html"

    def get(self, request):
       
        return render(request, self.template)


class ContactSupport(View):
    contact_template = app + 'contact_us.html'
    support_template = app + 'support.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.full_name if request.user.full_name else '',
                'email': request.user.email if request.user.email else '',
                'contact': request.user.contact if request.user.contact else '',
            }
            template = self.support_template
        else:
            initial_data = {
                'name': '',
                'email': '',
                'contact': '',
            }
            template = self.contact_template

        form = forms.ContactMessageForm(initial=initial_data)
        return render(request, template, {'form': form})

    def post(self, request, *args, **kwargs):
        form = forms.ContactMessageForm(request.POST)
        if form.is_valid():
            # Create a new ContactMessage instance
            contact_message = ContactMessage(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                contact=form.cleaned_data['contact'],
                message=form.cleaned_data['message']
            )
            
            # Associate the message with the authenticated user if available
            if request.user.is_authenticated:
                contact_message.user = request.user
            
            contact_message.save()

            if request.user.is_authenticated:
                messages.success(request, 'Your support request has been sent successfully.')
                return redirect('app_common:contact_support')
            else:
                messages.success(request, 'Your message has been sent successfully.')
                return redirect('app_common:contact_support')

        template = self.support_template if request.user.is_authenticated else self.contact_template
        return render(request, template, {'form': form})

class TermsConditions(View):
    template = app + "terms_conditions.html"

    def get(self, request):
       
        return render(request, self.template)

class PrivacyPolicy(View):
    template = app + "privacy_policy.html"

    def get(self, request):
       
        return render(request, self.template)

class ReturnPolicy(View):
    template = app + "return_policy.html"

    def get(self, request):
       
        return render(request, self.template)

class OurServices(View):
    template = app + "our_services.html"

    def get(self, request):
       
        return render(request, self.template)
class LocateUs(View):
    template = app + "locate_us.html"

    def get(self, request):
       
        return render(request, self.template)