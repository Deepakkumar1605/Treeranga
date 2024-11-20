from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.contrib import messages
from django.utils.decorators import method_decorator
from app_common.error import render_error_page
from helpers import utils
from app_common.models import ContactMessage,Banner, Sectionbanner, FAQ
from app_common.forms import ReplyForm,BannerForm
from users.user_views.emails import send_template_email
from app_common import forms
from app_common import models


app = 'app_common/'

class AdminMessageListView(View):
    template = app + 'admin/message_list.html'

    def get(self, request, *args, **kwargs):
        try:
            messages_list = ContactMessage.objects.all().order_by('-created_at')
            paginator = Paginator(messages_list, 10)  # Show 10 messages per page
            page_number = request.GET.get('page')
            messages = paginator.get_page(page_number)
            return render(request, self.template, {'messages': messages})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


class AdminMessageDetailView(View):
    template = app +'admin/message_detail.html'

    def get(self, request, message_id, *args, **kwargs):
        try:
            message = get_object_or_404(ContactMessage, id=message_id)
            form = ReplyForm()
            return render(request, self.template, {'message': message, 'form': form})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request, message_id, *args, **kwargs):
        try:
            message = get_object_or_404(ContactMessage, id=message_id)
            form = ReplyForm(request.POST)
            if form.is_valid():
                reply = form.cleaned_data['reply']

                # Send the reply via email using the template function
                context = {
                    'user_name': message.name,
                    'reply_message': reply,
                }
                send_template_email(
                    subject='Reply to Your Contact Message',
                    template_name='users/email/contact_message_reply.html',
                    context=context,
                    recipient_list=[message.email]
                )

                messages.success(request, 'Reply sent successfully.')
                return redirect('app_common:admin_message_list')

            return render(request, self.template, {'message': message, 'form': form})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


@method_decorator(utils.super_admin_only, name='dispatch')
class BannerList(View):
    template = app +"admin/banner.html"
    model = Banner
    form_class = BannerForm

    def get(self, request):
        try:
            banner_list = self.model.objects.all().order_by('order')  
            form = self.form_class()
            context = {
                "banner_list": banner_list,
                "form": form,
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request):
        try:
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Banner added successfully.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            return redirect('app_common:web_banner_list')
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

@method_decorator(utils.super_admin_only, name='dispatch')
class BannerEdit(View):
    form_class = BannerForm
    model = Banner

    def get(self, request, banner_id):
        banner = get_object_or_404(self.model, id=banner_id)
        form = self.form_class(instance=banner)
        return render(request, 'path/to/edit_banner.html', {'form': form, 'banner': banner})

    def post(self, request, banner_id):
        banner = get_object_or_404(self.model, id=banner_id)
        form = self.form_class(request.POST, request.FILES, instance=banner)

        if form.is_valid():
            form.save()
            messages.success(request, 'Banner updated successfully.')
            return redirect('app_common:web_banner_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return redirect('app_common:web_banner_list')


@method_decorator(utils.super_admin_only, name='dispatch')
class BannerDelete(View):
    model = Banner

    def get(self, request, banner_id):
        try:
            banner = get_object_or_404(self.model, id=banner_id)
            if banner.image:
                image_path = banner.image.path
                default_storage.delete(image_path)  # Delete the image from storage
                banner.image = None

            banner.delete()
            messages.success(request, 'Banner deleted successfully.')
            return redirect('app_common:web_banner_list')
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)



class CreateNotificationView(View):
    template_name =app + 'admin/create_notification.html'

    def get(self, request):
        form = forms.NotificationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = forms.NotificationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification added successfully!")
            return redirect('app_common:admin_notification_list')  # Redirect to a notification list or another page
        else:
            messages.error(request, "Error adding notification. Please check the form.")
        
        return render(request, self.template_name, {'form': form})
    
    
    
class AdminNotificationListView(View):
    template = app + 'admin/admin_notification_list.html'  # Make sure to create this template

    def get(self, request):
        try:
            # Fetch all notifications
            notifications_list = models.Notification.objects.all().order_by('-date')
            
            # Set up pagination with 10 notifications per page
            paginator = Paginator(notifications_list, 10)
            page_number = request.GET.get('page')
            notifications = paginator.get_page(page_number)

            # Render the notifications in the template
            return render(request, self.template, {'notifications': notifications})
        except Exception as e:
            # Handle any errors by displaying an error message
            error_message = f"An unexpected error occurred: {str(e)}"
            return render(request, 'error_page.html', {'error_message': error_message}, status=400)
        
        
        
        
class AdminNotificationUpdateView(View):
    template_name = app +'admin/update_notification.html'  # Path to your update template

    def get(self, request, pk):
        notification = get_object_or_404(models.Notification, pk=pk)
        form = forms.NotificationForm(instance=notification)
        return render(request, self.template_name, {'form': form, 'notification': notification})

    def post(self, request, pk, ):
        notification = get_object_or_404(models.Notification, pk=pk)
        form = forms.NotificationForm(request.POST, instance=notification)
        if form.is_valid():
            form.save()
            return redirect('app_common:admin_notification_list')  # Adjust with the correct URL name for listing notifications
        return render(request, self.template_name, {'form': form, 'notification': notification})
    
    
    
class AdminNotificationDeleteView(View):
    template_name = app +'admin/confirm_delete_notification.html'  # Path to your delete confirmation template

    def get(self, request, pk, *args, **kwargs):
        notification = get_object_or_404(models.Notification, pk=pk)
        return render(request, self.template_name, {'notification': notification})

    def post(self, request, pk, *args, **kwargs):
        notification = get_object_or_404(models.Notification, pk=pk)
        notification.delete()
        return redirect('app_common:admin_notification_list')  # Adjust with the correct URL name for listing notifications


@method_decorator(utils.super_admin_only, name='dispatch')
class SectionBannerList(View):
    template =app + "admin/sectionbanner.html"  # Ensure this path matches your templates folder structure
    model = Sectionbanner
    form_class = forms.SectionBannerForm

    def get(self, request):
        try:
            banner_list = self.model.objects.all()  
            form = self.form_class()
            context = {
                "banner_list": banner_list,
                "form": form,
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request):
        try:
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Banner added successfully.")
            else:
                # Loop through form errors and display each error
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            return redirect('app_common:section_banner_list')
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
        
        
@method_decorator(utils.super_admin_only, name='dispatch')
class SectionBannerEdit(View):
    form_class = forms.SectionBannerForm
    model = Sectionbanner

    def get(self, request, banner_id):
        banner = get_object_or_404(self.model, id=banner_id)
        form = self.form_class(instance=banner)
        return render(request, 'path/to/edit_banner.html', {'form': form, 'banner': banner})

    def post(self, request, banner_id):
        banner = get_object_or_404(self.model, id=banner_id)
        form = self.form_class(request.POST, request.FILES, instance=banner)

        if form.is_valid():
            form.save()
            messages.success(request, 'Banner updated successfully.')
            return redirect('app_common:section_banner_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return redirect('app_common:section_banner_list')
        
        
@method_decorator(utils.super_admin_only, name='dispatch')
class BannerDelete(View):
    model = Sectionbanner

    def get(self, request, banner_id):
        try:
            banner = get_object_or_404(self.model, id=banner_id)
            if banner.image:
                image_path = banner.image.path
                default_storage.delete(image_path)  # Delete the image from storage
                banner.image = None

            banner.delete()
            messages.success(request, 'Banner deleted successfully.')
            return redirect('app_common:section_banner_list')
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
        
        
        
class FAQCreateView(View):
    template_name = app + "admin/faq_create.html" 
    model = FAQ
    def get(self, request):
        
        faq_list = FAQ.objects.all().order_by('id') 
        form = forms.FAQForm()
        return render(request, self.template_name, {'form': form, 'faq_list': faq_list})

    def post(self, request):
        form = forms.FAQForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "FAQ added successfully!")
            return redirect('app_common:add_faq')  # Adjust this with the actual URL name for listing FAQs
        return render(request, self.template_name, {'form': form})
          
        
@method_decorator(utils.super_admin_only, name='dispatch')
class FAQedit(View):
    form_class = forms.FAQForm 
    model = models.FAQ 

    def get(self, request, faq_id):
        faq_list = get_object_or_404(self.model, id=faq_id)
        form = self.form_class(instance=faq_list)
        return render(request, 'path/to/faq_create.html', {'form': form, 'faq_list': faq_list})

    def post(self, request, faq_id):
        faq_list = get_object_or_404(self.model, id=faq_id)
        form = self.form_class(request.POST, instance=faq_list)

        if form.is_valid():
            form.save()
            messages.success(request, 'FAQ updated successfully.')
            return redirect('app_common:add_faq')  # Replace with your actual URL name for listing FAQs
        return render(request, 'path/to/faq_create.html', {'form': form, 'faq_list': faq_list})
    
    
@method_decorator(utils.super_admin_only, name='dispatch')
class FAQDelete(View):
    model = FAQ

    def get(self, request, faq_id):
        try:
            faq_list = get_object_or_404(self.model, id=faq_id)

            faq_list.delete()
            messages.success(request, 'faq deleted successfully.')
            return redirect('app_common:add_faq')
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)