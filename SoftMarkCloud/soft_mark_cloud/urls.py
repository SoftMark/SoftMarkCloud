from django.urls import path
from . import views
urlpatterns = [
    path('register_user', views.sign_up, name='register'),
    path('login_user', views.sign_in, name='login'),
    path('logout_user', views.sign_out, name='logout'),
]
