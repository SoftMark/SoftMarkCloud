from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('account_manager/', views.account_manager, name='account_manager'),
    path('cloud_view/', views.cloud_view, name='cloud_view'),
    path('deploy/', views.deployer, name='deployer'),
    path('register/', views.sign_up, name='register'),
    path('login/', views.sign_in, name='login'),
    path('logout/', views.logout_user, name='logout')
]
