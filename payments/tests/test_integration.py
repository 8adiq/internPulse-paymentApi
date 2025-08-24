import pytest
from unittest.mock import patch
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from payments.models import Payment

@pytest.mark.django_db
class TestPaymentIntegration:
    """Integration tests for complete payment flow"""
    
    @pytest.fixture
    def api_client(self):
        """Fixture for API client"""
        return APIClient()
    
    @pytest.fixture
    def valid_payment_data(self):
        """Fixture for valid payment data"""
        return {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'phone_number': '1234567890',
            'state': 'Lagos',
            'country': 'Nigeria',
            'amount': '50.00',
            'currency': 'NGN'
        }
    
    @patch('payments.service.PaystackService.initiate_payment')
    def test_complete_payment_flow(self, mock_paystack, api_client, valid_payment_data):
        """Test complete payment flow from creation to status check"""
        # Mock Paystack response
        mock_paystack.return_value = {
            'success': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/abc123',
                'reference': 'PAY-TEST123'
            }
        }
        
        # Step 1: Create payment
        response = api_client.post('/api/v1/payments/', valid_payment_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'success'
        payment_id = response.data['payment']['id']
        
        # Step 2: Get payment status
        response = api_client.get(f'/api/v1/payments/{payment_id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['payment']['id'] == payment_id
        assert response.data['payment']['customer_name'] == 'John Doe'
        assert response.data['payment']['status'] == 'pending'
    
    @patch('payments.service.PaystackService.initiate_payment')
    def test_payment_creation_with_paystack_integration(self, mock_paystack, api_client, valid_payment_data):
        """Test payment creation with actual Paystack integration"""
        # Mock Paystack response
        mock_paystack.return_value = {
            'success': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/abc123',
                'reference': 'PAY-TEST123'
            }
        }
        
        # Create payment
        response = api_client.post('/api/v1/payments/', valid_payment_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['payment']['paystack_authorization_url'] == 'https://checkout.paystack.com/abc123'
        
        # Verify payment was saved to database
        payment = Payment.objects.get(customer_email='john@example.com')
        assert payment.paystack_authorization_url == 'https://checkout.paystack.com/abc123'
        assert payment.paystack_reference == 'PAY-TEST123'
    
    def test_payment_validation_flow(self, api_client):
        """Test payment validation flow"""
        # Test with missing required fields
        invalid_data = {
            'customer_name': 'John Doe',
            'amount': '50.00'
            # Missing email, phone, etc.
        }
        
        response = api_client.post('/api/v1/payments/', invalid_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == 'error'
        assert 'customer_email' in response.data['errors']
        assert 'phone_number' in response.data['errors']
        assert 'state' in response.data['errors']
        assert 'country' in response.data['errors']
    
    def test_payment_status_retrieval_flow(self, api_client):
        """Test payment status retrieval flow"""
        # Create a payment directly in database
        payment = Payment.objects.create(
            customer_name='Jane Doe',
            customer_email='jane@example.com',
            phone_number='0987654321',
            state='Abuja',
            country='Nigeria',
            amount=Decimal('100.00'),
            currency='NGN',
            status='completed'
        )
        
        # Retrieve payment status
        response = api_client.get(f'/api/v1/payments/{payment.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['payment']['id'] == str(payment.id)
        assert response.data['payment']['customer_name'] == 'Jane Doe'
        assert response.data['payment']['status'] == 'completed'
        assert response.data['payment']['amount'] == '100.00'
    
    def test_webhook_integration_flow(self, api_client):
        """Test webhook integration flow"""
        # Create a payment first
        payment = Payment.objects.create(
            customer_name='Test User',
            customer_email='test@example.com',
            phone_number='1234567890',
            state='Lagos',
            country='Nigeria',
            amount=Decimal('75.00'),
            currency='NGN',
            paystack_reference='PAY-WEBHOOK123'
        )
        
        # Simulate webhook from Paystack
        webhook_data = {
            'event': 'charge.success',
            'data': {
                'reference': 'PAY-WEBHOOK123',
                'status': 'success',
                'amount': 7500,
                'id': 987654321
            }
        }
        
        response = api_client.post(
            '/api/v1/payments/webhook/paystack/',
            webhook_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        
        # Verify payment was updated
        payment.refresh_from_db()
        assert payment.status == 'completed'
        assert payment.paystack_transaction_id == '987654321'
    
    def test_multiple_payments_flow(self, api_client):
        """Test handling multiple payments"""
        # Create multiple payments
        payments_data = [
            {
                'customer_name': 'User 1',
                'customer_email': 'user1@example.com',
                'phone_number': '1111111111',
                'state': 'Lagos',
                'country': 'Nigeria',
                'amount': '25.00',
                'currency': 'NGN'
            },
            {
                'customer_name': 'User 2',
                'customer_email': 'user2@example.com',
                'phone_number': '2222222222',
                'state': 'Abuja',
                'country': 'Nigeria',
                'amount': '50.00',
                'currency': 'NGN'
            }
        ]
        
        payment_ids = []
        
        for payment_data in payments_data:
            response = api_client.post('/api/v1/payments/', payment_data, format='json')
            assert response.status_code == status.HTTP_201_CREATED
            payment_ids.append(response.data['payment']['id'])
        
        # Verify all payments were created
        assert len(payment_ids) == 2
        
        # Retrieve each payment
        for payment_id in payment_ids:
            response = api_client.get(f'/api/v1/payments/{payment_id}/')
            assert response.status_code == status.HTTP_200_OK
            assert response.data['payment']['id'] == payment_id
    
    def test_payment_error_handling_flow(self, api_client):
        """Test error handling in payment flow"""
        # Test with invalid UUID
        invalid_id = 'not-a-uuid'
        response = api_client.get(f'/api/v1/payments/{invalid_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test with non-existent UUID
        import uuid
        fake_id = str(uuid.uuid4())
        response = api_client.get(f'/api/v1/payments/{fake_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test with invalid payment data
        invalid_data = {
            'customer_name': 'Test User',
            'customer_email': 'invalid-email',
            'phone_number': '1234567890',
            'state': 'Lagos',
            'country': 'Nigeria',
            'amount': '-10.00',  # Negative amount
            'currency': 'NGN'
        }
        
        response = api_client.post('/api/v1/payments/', invalid_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_api_versioning_integration(self, api_client):
        """Test API versioning integration"""
        # Test v1 endpoints work
        response = api_client.get('/api/v1/payments/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED  # Method not allowed, not 404
        
        # Test non-versioned endpoints don't work
        response = api_client.get('/api/payments/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test wrong version
        response = api_client.get('/api/v2/payments/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_payment_database_integration(self, api_client, valid_payment_data):
        """Test database integration for payments"""
        # Create payment
        response = api_client.post('/api/v1/payments/', valid_payment_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        payment_id = response.data['payment']['id']
        
        # Verify payment exists in database
        payment = Payment.objects.get(id=payment_id)
        assert payment.customer_name == 'John Doe'
        assert payment.customer_email == 'john@example.com'
        assert payment.amount == Decimal('50.00')
        assert payment.status == 'pending'
        
        # Update payment status directly in database
        payment.status = 'completed'
        payment.save()
        
        # Verify status change is reflected in API
        response = api_client.get(f'/api/v1/payments/{payment_id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['payment']['status'] == 'completed'
    
    def test_webhook_error_handling_integration(self, api_client):
        """Test webhook error handling integration"""
        # Test webhook with invalid data
        invalid_webhook_data = {
            'invalid': 'data'
        }
        
        response = api_client.post(
            '/api/v1/payments/webhook/paystack/',
            invalid_webhook_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == 'error'
        
        # Test webhook with non-existent payment reference
        webhook_data = {
            'event': 'charge.success',
            'data': {
                'reference': 'PAY-NONEXISTENT',
                'status': 'success',
                'amount': 5000,
                'id': 123456789
            }
        }
        
        response = api_client.post(
            '/api/v1/payments/webhook/paystack/',
            webhook_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == 'error'
    
    def test_payment_serialization_integration(self, api_client, valid_payment_data):
        """Test payment serialization integration"""
        # Create payment
        response = api_client.post('/api/v1/payments/', valid_payment_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        payment_data = response.data['payment']
        
        # Verify all required fields are present
        required_fields = [
            'id', 'customer_name', 'customer_email', 'phone_number',
            'state', 'country', 'amount', 'currency', 'status'
        ]
        
        for field in required_fields:
            assert field in payment_data
        
        # Verify data types
        assert isinstance(payment_data['id'], str)
        assert isinstance(payment_data['customer_name'], str)
        assert isinstance(payment_data['customer_email'], str)
        assert isinstance(payment_data['amount'], str)
        assert isinstance(payment_data['status'], str)
        
        # Verify UUID format
        import uuid
        try:
            uuid.UUID(payment_data['id'])
        except ValueError:
            pytest.fail("Payment ID is not a valid UUID")
    
    def test_concurrent_payment_creation(self, api_client):
        """Test concurrent payment creation"""
        import threading
        import time
        
        results = []
        
        def create_payment(thread_id):
            payment_data = {
                'customer_name': f'User {thread_id}',
                'customer_email': f'user{thread_id}@example.com',
                'phone_number': f'123456789{thread_id}',
                'state': 'Lagos',
                'country': 'Nigeria',
                'amount': '25.00',
                'currency': 'NGN'
            }
            
            response = api_client.post('/api/v1/payments/', payment_data, format='json')
            results.append({
                'thread_id': thread_id,
                'status_code': response.status_code,
                'success': response.status_code == status.HTTP_201_CREATED
            })
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_payment, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all payments were created successfully
        successful_payments = [r for r in results if r['success']]
        assert len(successful_payments) == 5
        
        # Verify all payments are in database
        assert Payment.objects.count() == 5
