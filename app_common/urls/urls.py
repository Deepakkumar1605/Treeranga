from django.urls import path
from app_common import views
from django.conf import settings
from django.conf.urls.static import static
from app_common.app_common_views import app_common_views,admin_views


app_name = 'app_common'



urlpatterns = [
    # static pages
    path('', app_common_views.HomeView.as_view(), name='home'),
    path('AboutUs/',app_common_views.AboutUs.as_view(),name="about_us"),    
    path('ContactUs/',app_common_views.ContactSupport.as_view(),name="contact_support"),
    path('Terms&Conditions/',app_common_views.TermsConditions.as_view(),name="terms_conditions"),
    path('Privacy&policy/',app_common_views.PrivacyPolicy.as_view(),name="privacy_policy"),
    path('RetrunPolicy/',app_common_views.ReturnPolicy.as_view(),name="retrun_policy"),
    path('OurServices/',app_common_views.OurServices.as_view(),name="our_services"),
    path('LocateUs/',app_common_views.LocateUs.as_view(),name="locate_us"),

    #admin message 
    path('Admin/Messages/', admin_views.AdminMessageListView.as_view(), name='admin_message_list'),
    path('Admin/Messages/<int:message_id>/', admin_views.AdminMessageDetailView.as_view(), name='admin_message_detail'),


    #admin banner management
    path('Banners/', admin_views.BannerList.as_view(), name='web_banner_list'),
    path('banners/edit/<int:banner_id>/', admin_views.BannerEdit.as_view(), name='web_banner_edit'),
    path('Banners/delete/<int:banner_id>/', admin_views.BannerDelete.as_view(), name='web_banner_delete'),
    
    
    path('admin/create-notification/', admin_views.CreateNotificationView.as_view(), name='create_notification'),
    path('admin/notifications/', admin_views.AdminNotificationListView.as_view(), name='admin_notification_list'),
    path('notifications/update/<int:pk>/', admin_views.AdminNotificationUpdateView.as_view(), name='update_notification'),
    path('notifications/delete/<int:pk>/', admin_views.AdminNotificationDeleteView.as_view(), name='delete_notification'),

] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)