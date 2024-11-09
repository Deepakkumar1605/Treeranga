from django.urls import path
from orders.orders_views import admin_orders_views,user_orders_views

app_name = 'orders'




urlpatterns = [


    #admin/orders
    path('AdminOrderList', admin_orders_views.OrderList.as_view(), name='order_list'),
    path('AdminOrderSearch', admin_orders_views.OrderSearch.as_view(), name='admin_order_search'),
    path('AdminOrderDetail/<str:order_uid>', admin_orders_views.AdminOrderDetail.as_view(), name='admin_order_details'),
    path('AdminInvoceDownload/<str:order_uid>', admin_orders_views.DownloadInvoice.as_view(), name='download_invoice'),
    path('OrderStatusSearch', admin_orders_views.OrderStatusSearch.as_view(), name='order_status_search'),

    #user/order
    path('MyOders/',user_orders_views.UserOrder.as_view(),name='orders'),
    path('Orderdetail/<str:order_uid>', user_orders_views.OrderDetail.as_view(), name='order_detail'),
    
    path('DownloadInvoice/<str:order_uid>', user_orders_views.UserDownloadInvoice.as_view(), name='user_download_invoice'),

]