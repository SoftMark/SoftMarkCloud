from django.urls import path
from . import views
urlpatterns = [
    path('register_user', views.sign_in, name='register'),
    path('login_user', views.login, name='login'),
    path('logout_user', views.logout, name='logout'),
]
