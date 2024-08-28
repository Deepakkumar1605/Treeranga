from django.urls import path
from payment.payment_views import user_payment_views

app_name = 'payment'




urlpatterns = [
    path('paymentsuccess/',user_payment_views.PaymentSuccess.as_view(),name='paymentsuccess'),
    path('payment_success/',user_payment_views.SuccessPage.as_view(),name='success_payment'),
    
]