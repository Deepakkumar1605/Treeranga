from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from helpers import utils
from app_common.models import ContactMessage,Banner
from app_common.forms import ReplyForm,BannerForm
from users.user_views.emails import send_template_email


app = 'app_common/'

class AdminMessageListView(View):
    template = app +'admin/message_list.html'

    def get(self, request, *args, **kwargs):
        messages = ContactMessage.objects.all().order_by('-created_at')
        return render(request, self.template, {'messages': messages})

class AdminMessageDetailView(View):
    template = app +'admin/message_detail.html'

    def get(self, request, message_id, *args, **kwargs):
        message = get_object_or_404(ContactMessage, id=message_id)
        form = ReplyForm()
        return render(request, self.template, {'message': message, 'form': form})

    def post(self, request, message_id, *args, **kwargs):
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



@method_decorator(utils.super_admin_only, name='dispatch')
class BannerList(View):
    template = app +"admin/banner.html"  # Adjust the path as necessary
    model = Banner
    form_class = BannerForm

    def get(self, request):
        banner_list = self.model.objects.all().order_by('order')  # Order by 'order' field
        form = self.form_class()
        context = {
            "banner_list": banner_list,
            "form": form,
        }
        return render(request, self.template, context)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Banner added successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        return redirect('app_common:web_banner_list')



@method_decorator(utils.super_admin_only, name='dispatch')
class BannerDelete(View):
    model = Banner

    def get(self, request, banner_id):
        banner = get_object_or_404(self.model, id=banner_id)
        if banner.image:
            image_path = banner.image.path
            default_storage.delete(image_path)  # Delete the image from storage
            banner.image = None
        
        banner.delete()
        messages.success(request, 'Banner deleted successfully.')

        return redirect('app_common:web_banner_list')