from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from app_common.error import render_error_page
from app_common.models import ContactMessage
from orders.models import Order
from product_variations.models import VariantProduct
from users.forms import LoginForm
from app_common.models import ContactMessage,Banner
from users.user_views.emails import send_template_email
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
        try:
            if request.user.is_superuser:
                return redirect('users:admin_dashboard')

            # Get all categories
            categories = Category.objects.all()[:5]

            # Banner
            banners=Banner.objects.filter(active=True).order_by('order')

            # Handle Trending Products (simple and variant)
            trending_products = []
            for product in Products.objects.filter(trending="yes").order_by('-id')[:5]:
                if product.product_type == "simple":
                    simple_product = SimpleProduct.objects.filter(product=product, is_visible=True).first()
                    if simple_product:
                        trending_products.append({
                            'product': product,
                            'simple_product': simple_product,
                            'variant': "no"
                        })
                elif product.product_type == "variant":
                    variant_product = VariantProduct.objects.filter(product=product, is_visible=True).first()
                    if variant_product:
                        trending_products.append({
                            'product': product,
                            'variant_product': variant_product,
                            'variant': "yes"
                        })

            # Handle New Products (simple and variant)
            new_products = []
            for product in Products.objects.filter(show_as_new="yes").order_by('-id')[:5]:
                if product.product_type == "simple":
                    simple_product = SimpleProduct.objects.filter(product=product, is_visible=True).first()
                    if simple_product:
                        new_products.append({
                            'product': product,
                            'simple_product': simple_product,
                            'variant': "no"
                        })
                elif product.product_type == "variant":
                    variant_product = VariantProduct.objects.filter(product=product, is_visible=True).first()
                    if variant_product:
                        new_products.append({
                            'product': product,
                            'variant_product': variant_product,
                            'variant': "yes"
                        })

            context = {
                'categories': categories,
                'banners': banners,
                'trending_products': trending_products,
                'new_products': new_products,
                'banners': banners,
                'MEDIA_URL': settings.MEDIA_URL,
            }
            return render(request, self.template, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class ContactSupport(View):
    contact_template = app + 'contact_us.html'
    support_template = app + 'support.html'

    def get(self, request, *args, **kwargs):
        try:
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

            form = ContactMessageForm(initial=initial_data)
            return render(request, template, {'form': form})

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request, *args, **kwargs):
        try:
            form = ContactMessageForm(request.POST)
            if form.is_valid():
                # Create a new ContactMessage instance
                contact_message = ContactMessage(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    contact=form.cleaned_data['contact'],
                    message=form.cleaned_data['message']
                )

                if request.user.is_authenticated:
                    contact_message.user = request.user

                contact_message.save()

                # Prepare email context for the confirmation email
                context = {
                    'user_name': contact_message.name,
                    'message_content': contact_message.message,
                }

                # Send confirmation email to the user
                send_template_email(
                    subject='Thank You for Contacting Us',
                    template_name='users/email/contact_message_confirmation.html',
                    context=context,
                    recipient_list=[contact_message.email]
                )

                # Set success message and redirect based on authentication
                success_message = 'Your support request has been sent successfully.' if request.user.is_authenticated else 'Your message has been sent successfully.'
                messages.success(request, success_message)
                return redirect('app_common:contact_support')

            template = self.support_template if request.user.is_authenticated else self.contact_template
            return render(request, template, {'form': form})

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class AboutUs(View):
    template = app + "about_us.html"

    def get(self, request):
        try:
            return render(request, self.template)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class TermsConditions(View):
    template = app + "terms_conditions.html"

    def get(self, request):
        try:
            return render(request, self.template)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class PrivacyPolicy(View):
    template = app + "privacy_policy.html"

    def get(self, request):
        try:
            return render(request, self.template)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class ReturnPolicy(View):
    template = app + "return_policy.html"

    def get(self, request):
        try:
            return render(request, self.template)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class OurServices(View):
    template = app + "our_services.html"

    def get(self, request):
        try:
            return render(request, self.template)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class LocateUs(View):
    template = app + "locate_us.html"

    def get(self, request):
        try:
            return render(request, self.template)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
