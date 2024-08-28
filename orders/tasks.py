from celery import shared_task
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import get_template

@shared_task
def update_order_status(email,data):

    html_tpl_path = 'app_common/checkout/invoice.html'


    for product in data['products']:
        product['product']['quantity']=product['quantity']

    context ={
        'order':data,
        'address':data['address'],
        'product_list':data['products'],
        'charges':data['order_meta_data']['charges'],
        'gross_amt':data['order_meta_data']['our_price'],
        'discount':data['order_meta_data']['our_price'] - data['order_value'],
    }
    email_html_template = get_template(html_tpl_path).render(context)

    subject = 'Order Update - LakshmiMart'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email, 'lakshmimart.tapas@gmail.com',]
    email_msg=EmailMessage( subject, email_html_template, email_from, recipient_list )
    email_msg.content_subtype = 'html'

    
    try:
        email_msg.send(fail_silently=False)
    except Exception as e:
        print("#############################################")
        print(str(e))
        print("#############################################")
    
    try:
        email_msg.send(fail_silently=False)
    except Exception as e:
        print("#############################################")
        print(str(e))
        print("#############################################")




@shared_task
def share_invoice(email,data):

    html_tpl_path = 'app_common/checkout/invoice.html'


    for product in data['products']:
        product['product']['quantity']=product['quantity']

    context ={
        'order':data,
        'address':data['address'],
        'product_list':data['products'],
        'charges':data['order_meta_data']['charges'],
        'gross_amt':data['order_meta_data']['our_price'],
        'discount':data['order_meta_data']['our_price'] - data['order_value'],
    }
    email_html_template = get_template(html_tpl_path).render(context)

    subject = 'Invoice - LakshmiMart'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email, 'lakshmimart.tapas@gmail.com',]
    email_msg=EmailMessage( subject, email_html_template, email_from, recipient_list )
    email_msg.content_subtype = 'html'

    
    try:
        email_msg.send(fail_silently=False)
    except Exception as e:
        print("#############################################")
        print(str(e))
        print("#############################################")