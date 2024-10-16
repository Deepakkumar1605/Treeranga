from django.urls import path
from app_common.app_common_views import api_views_app_common

urlpatterns = [ 
    
    path('api/home/', api_views_app_common.HomeAPIView.as_view(), name='api-home'),

]