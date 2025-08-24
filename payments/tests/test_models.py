import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from payments.models import Payment
import uuid

@pytest.mark.django_db
class TestPaymentModel:
    """Test cases for Payment model using pytest"""
    
    @pytest.fixture
    def valid_payment_data(self):
        """Fixture that provides valid payment data"""
        return {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'phone_number': '1234567890',
            'state': 'Lagos',
            'country': 'Nigeria',
            'amount': Decimal('50.00'),
            'currency': 'NGN'
        }
    
    def test_create_payment_with_valid_data(self, valid_payment_data):
        """Test creating a payment with valid data"""
        payment = Payment.objects.create(**valid_payment_data)
        
        assert payment.id is not None
        assert payment.customer_name == 'John Doe'
        assert payment.customer_email == 'john@example.com'
        assert payment.phone_number == '1234567890'
        assert payment.state == 'Lagos'
        assert payment.country == 'Nigeria'
        assert payment.amount == Decimal('50.00')
        assert payment.currency == 'NGN'
        assert payment.status == 'pending'
        assert payment.created_at is not None
        assert payment.updated_at is not None
    
    def test_payment_uuid_primary_key(self, valid_payment_data):
        """Test that payment uses UUID as primary key"""
        payment = Payment.objects.create(**valid_payment_data)
        
        assert isinstance(payment.id, uuid.UUID)
        assert payment.id != uuid.uuid4()  # Should be unique
    
    @pytest.mark.parametrize("amount,expected_valid", [
        (Decimal('0.01'), True),   # Minimum amount
        (Decimal('100.00'), True), # Normal amount
        (Decimal('999999.99'), True), # Large amount
        (Decimal('0.00'), False),  # Too low
        (Decimal('-10.00'), False), # Negative
    ])
    def test_payment_amount_validation(self, amount, expected_valid, valid_payment_data):
        """Test amount validation with different values"""
        valid_payment_data['amount'] = amount
        
        if expected_valid:
            payment = Payment.objects.create(**valid_payment_data)
            assert payment.amount == amount
        else:
            with pytest.raises(ValidationError):
                payment = Payment(**valid_payment_data)
                payment.full_clean()
    
    @pytest.mark.parametrize("email,expected_valid", [
        ('test@example.com', True),
        ('user.name@domain.co.uk', True),
        ('invalid-email', False),
        ('@domain.com', False),
        ('user@', False),
        ('', False),
    ])
    def test_payment_email_validation(self, email, expected_valid, valid_payment_data):
        """Test email validation"""
        valid_payment_data['customer_email'] = email
        
        if expected_valid:
            payment = Payment.objects.create(**valid_payment_data)
            assert payment.customer_email == email
        else:
            with pytest.raises(ValidationError):
                payment = Payment(**valid_payment_data)
                payment.full_clean()
    
    def test_payment_string_representation(self, valid_payment_data):
        """Test string representation of payment"""
        payment = Payment.objects.create(**valid_payment_data)
        expected_str = f"John Doe - 50.00 NGN (pending)"
        assert str(payment) == expected_str
    
    def test_payment_ordering(self, valid_payment_data):
        """Test that payments are ordered by created_at descending"""
        payment1 = Payment.objects.create(**valid_payment_data)
        
        # Create second payment with different data
        payment2_data = valid_payment_data.copy()
        payment2_data.update({
            'customer_name': 'Jane Doe',
            'customer_email': 'jane@example.com',
            'phone_number': '0987654321',
            'state': 'Abuja',
            'country': 'Nigeria',
            'amount': Decimal('100.00'),
        })
        payment2 = Payment.objects.create(**payment2_data)
        
        payments = Payment.objects.all()
        assert payments[0] == payment2  # Most recent first
        assert payments[1] == payment1
    
    @pytest.mark.parametrize("status", [
        'pending',
        'processing',
        'completed',
        'failed',
        'cancelled',
    ])
    def test_payment_status_choices(self, status, valid_payment_data):
        """Test payment status choices"""
        payment = Payment.objects.create(**valid_payment_data)
        payment.status = status
        payment.save()
        
        payment.refresh_from_db()
        assert payment.status == status
    
    def test_payment_default_values(self, valid_payment_data):
        """Test default values for payment fields"""
        payment = Payment.objects.create(**valid_payment_data)
        
        assert payment.currency == 'NGN'  # Default currency
        assert payment.status == 'pending'  # Default status
        assert payment.paystack_reference is None  # Should be None initially
        assert payment.paystack_transaction_id is None  # Should be None initially
        assert payment.paystack_authorization_url is None  # Should be None initially
    
    def test_payment_field_lengths(self, valid_payment_data):
        """Test field length constraints"""
        # Test customer_name max length
        long_name = 'A' * 256  # Exceeds max_length=255
        valid_payment_data['customer_name'] = long_name
        
        with pytest.raises(ValidationError):
            payment = Payment(**valid_payment_data)
            payment.full_clean()
        
        # Test phone_number max length
        long_phone = '1' * 21  # Exceeds max_length=20
        valid_payment_data['customer_name'] = 'John Doe'  # Reset to valid
        valid_payment_data['phone_number'] = long_phone
        
        with pytest.raises(ValidationError):
            payment = Payment(**valid_payment_data)
            payment.full_clean()
    
    def test_payment_meta_options(self, valid_payment_data):
        """Test model meta options"""
        payment = Payment.objects.create(**valid_payment_data)
        
        # Test verbose names
        assert Payment._meta.verbose_name == 'Payment'
        assert Payment._meta.verbose_name_plural == 'Payments'
        
        # Test ordering
        assert Payment._meta.ordering == ['-created_at']
    
    def test_payment_blank_null_fields(self, valid_payment_data):
        """Test that optional fields can be blank/null"""
        payment = Payment.objects.create(**valid_payment_data)
        
        # These fields should allow blank/null
        payment.paystack_reference = ''
        payment.paystack_transaction_id = ''
        payment.paystack_authorization_url = ''
        payment.save()
        
        payment.refresh_from_db()
        assert payment.paystack_reference == ''
        assert payment.paystack_transaction_id == ''
        assert payment.paystack_authorization_url == ''
    
    def test_payment_decimal_precision(self, valid_payment_data):
        """Test decimal field precision"""
        # Test with different decimal places
        payment = Payment.objects.create(**valid_payment_data)
        
        # Should handle 2 decimal places
        payment.amount = Decimal('123.45')
        payment.save()
        
        payment.refresh_from_db()
        assert payment.amount == Decimal('123.45')
        
        # Should handle 1 decimal place
        payment.amount = Decimal('123.4')
        payment.save()
        
        payment.refresh_from_db()
        assert payment.amount == Decimal('123.40')  # Django normalizes to 2 decimal places
