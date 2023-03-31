from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('register', views.sign_up, name='register'),
    path('login', views.sign_in, name='login'),
    path('logout', views.sign_out, name='logout'),
]
