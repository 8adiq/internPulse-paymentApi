from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.create_payment, name='create_payment'),
    path('<uuid:payment_id>/', views.get_payment_status, name='get_payment_status'),
    path('webhook/paystack/', views.paystack_webhook, name='paystack_webhook'),
]
