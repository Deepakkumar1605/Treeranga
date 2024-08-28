from django.urls import path
from blog.blog_views import admin_blog_views, user_blog_views

app_name = 'blog'

urlpatterns = [
    #admin
    path("blog_list", admin_blog_views.BlogList.as_view(), name="blog_list"),
    path("blog_search", admin_blog_views.BlogSearch.as_view(), name="blog_search"),
    path("blog_add", admin_blog_views.BlogAdd.as_view(), name="blog_add"),
    path("blog_update/<str:blog_id>", admin_blog_views.BlogUpdate.as_view(), name="blog_update"),
    path("blog_delete/<str:blog_id>", admin_blog_views.BlogDelete.as_view(), name="blog_delete"),

    #user
    path('user_blog_list/', user_blog_views.BlogCategory.as_view(), name='user_blog_list'),
    path('user_blog_details/<slug:slug>/', user_blog_views.BlogDetails.as_view(), name='user_blog_details'),


]

