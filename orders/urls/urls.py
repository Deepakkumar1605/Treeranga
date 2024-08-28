from django.urls import path
from orders.orders_views import admin_orders_views,user_orders_views

app_name = 'orders'




urlpatterns = [


    #admin/orders
    path('order/admin_order_list', admin_orders_views.OrderList.as_view(), name='order_list'),
    path('order/admin_order_search', admin_orders_views.OrderSearch.as_view(), name='admin_order_search'),
    path('order/admin_order_detail/<str:order_uid>', admin_orders_views.AdminOrderDetail.as_view(), name='admin_order_details'),
    path('order/download_invoice/<str:order_uid>', admin_orders_views.DownloadInvoice.as_view(), name='download_invoice'),
    path('order/order_status_search', admin_orders_views.OrderStatusSearch.as_view(), name='order_status_search'),

    #user/order
    path('your/oders/',user_orders_views.UserOrder.as_view(),name='orders'),
    path('order/order_detail/<str:order_uid>', user_orders_views.OrderDetail.as_view(), name='order_detail'),
    path('order/user_download_invoice/<str:order_uid>', user_orders_views.UserDownloadInvoice.as_view(), name='user_download_invoice'),

]