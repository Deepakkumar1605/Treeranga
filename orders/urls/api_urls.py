from django.urls import path
from orders.orders_views import api_orders_views

from django.contrib.auth import views 

app_name = 'orders'

urlpatterns = [
    path('api/user/orders/', api_orders_views.UserOrderAPIView.as_view(), name='user-orders'),
    path('api/order/<str:order_uid>/', api_orders_views.OrderDetailAPIView.as_view(), name='order-detail-api'),
    path('api/order', api_orders_views.OrderCreateView.as_view(), name='order-create-api'),


    path('user/orders/', api_orders_views.UserOrderAPIView.as_view(), name='user-orders'),  # Retrieve all user orders
    path('review/submit/', api_orders_views.SubmitReviewAPIView.as_view(), name='submit-review'),  # Submit a review for a product
    path('review/submit-page/<slug:slug>/', api_orders_views.SubmitReviewPageAPIView.as_view(), name='submit-review-page'),  # Retrieve review submission page data

]
