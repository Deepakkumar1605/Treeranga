from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.contrib import messages
from django.utils.decorators import method_decorator
from app_common.error import render_error_page
from helpers import utils
from app_common.models import ContactMessage,Banner
from app_common.forms import ReplyForm,BannerForm
from users.user_views.emails import send_template_email


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
            banner_list = self.model.objects.all().order_by('order')  # Order by 'order' field
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
