from django.urls import path
from users import views
from users import forms
from users.user_views import user_views,admin_views,authentication_views
from app_common.app_common_views import app_common_views
from django.contrib.auth import views as auth_view
app_name = 'users'


urlpatterns = [
    #Authentication urls
    path('admin/', admin_views.AdminDashboard.as_view(), name='admin_dashboard'),
    path('signup', authentication_views.Registration.as_view(), name = "signup"),
    path('login', authentication_views.Login.as_view(), name = "login"),
    path('ForgotPassword/', authentication_views.ForgotPasswordView.as_view(), name = "forgot_password"),
    path('Reset-Password/<uuid:token>/', authentication_views.ResetPasswordView.as_view(), name='reset_password'),  # Ensure this matches
    path('Logout/', authentication_views.Logout.as_view(), name = "logout"),
    path('AccountDeletion/', authentication_views.AccountDeletionView.as_view(), name='account_deletion'),


    #user
    path('Profile',user_views.ProfileView.as_view(),name="profile"),
    path('Updateprofile/',user_views.UpdateProfileView.as_view(),name="updateprofile"),
    path('Account-details',user_views.AccountDetails.as_view(),name='account_details'),
    path('Profile/alladdress',user_views.AllAddress.as_view(),name="alladdress"),
    path('Profile/addaddress',user_views.ProfileAddAddress.as_view(),name="profile_addaddress"),
    path('Profile/update-address/<str:address_id>/', user_views.ProfileUpdateAddress.as_view(), name='profile_update_address'),
    path('Profile/delete-address/<str:address_id>/', user_views.ProfileDeleteAddress.as_view(), name='profile_delete_address'),

    # admin 
    path("UsersList", admin_views.UserList.as_view(), name="userslist"),
    path('UserDetail/<int:user_id>', admin_views.UserDetailView.as_view(), name='user_detail'),
    path('DeleteUser/<int:user_id>/', admin_views.DeleteUser.as_view(), name='delete_user'),
    
]