from rest_framework import serializers
from .models import Payment


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serialiser for creating new payments"""

    class Meta:
        model = Payment
        fields = [
            'customer_name',
            'customer_email',
            'phone_number',
            'state',
            'country',
            'amount',
            'currency'
        ]

    def validate_amount(self,amount):
            """Custom validation for amount"""

            if amount<=0:
                raise serializers.ValidationError("Amount must be greater than zero")
            return amount
        
    def validate_currency(self,currency):
            """Custom validation for curreny"""
            if currency.upper() not in ['NGN','USD','GHC']:
                raise serializers.ValidationError("Currency must be NGN, USD, or GHS.")
            return currency.upper()
        
class PaymentDetailsSerializer(serializers.ModelSerializer):
    """Serializer for payment details (read only)"""
    class Meta:
        model = Payment
        fields = [
            'id',
            'customer_name',
            'customer_email',
            'phone_number',
            'state',
            'country',
            'amount',
            'currency',
            'status',
            'paystack_reference',
            'paystack_transaction_id',
            'paystack_authorization_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'paystack_reference', 'paystack_transaction_id', 'paystack_authorization_url', 'created_at',
            'updated_at'
        ]


class PaymentStatusSerializer(serializers.ModelSerializer):
    """Serilaizer for payment status updates"""

    class Meta:
        model = Payment
        fields = ['status']
        read_only_fields = ['status']