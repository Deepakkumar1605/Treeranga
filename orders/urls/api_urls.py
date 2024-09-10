from django.urls import path
from orders.orders_views import api_orders_views

from django.contrib.auth import views 

app_name = 'orders'

urlpatterns = [
    path('api/user/orders/', api_orders_views.UserOrderAPIView.as_view(), name='user-orders'),
    path('api/order/<str:order_uid>/', api_orders_views.OrderDetailAPIView.as_view(), name='order-detail-api'),


]