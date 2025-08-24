from django.db import models
import uuid
from django.core.validators import MinValueValidator
from decimal import Decimal

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3,default='NGN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paystack_reference = models.CharField(max_length=255, blank=True, null=True)
    paystack_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    paystack_authorization_url = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20,choices=PAYMENT_STATUS_CHOICES,default='pending')


    class Meta:
        ordering = ['-created_at'] 
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"{self.customer_name} - {self.amount} {self.currency} ({self.status})"
    

