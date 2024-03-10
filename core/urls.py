from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about-us/', views.about, name='about_us'),
    path('contact-us/', views.contactus, name='contact_us'),
    path('terms-and-condition/', views.termscondition, name='terms_and_condition'),
    path('privacy-policy/', views.privacypolicy, name='privacy_policy'),

]