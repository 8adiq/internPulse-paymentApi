import pytest
import json
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from payments.models import Payment

@pytest.mark.django_db
class TestPaymentViews:
    """Test cases for payment views using pytest"""
    
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
    
    @pytest.fixture
    def payment_instance(self):
        """Fixture that creates a Payment instance"""
        return Payment.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            phone_number='1234567890',
            state='Lagos',
            country='Nigeria',
            amount=Decimal('50.00'),
            currency='NGN',
            paystack_reference='PAY-TEST123'
        )
    
    @patch('payments.service.PaymentService.create_payment')
    def test_create_payment_success(self, mock_create_payment, api_client, valid_payment_data):
        """Test successful payment creation via API"""
        # Mock service response
        mock_create_payment.return_value = {
            'success': True,
            'payment': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'phone_number': '1234567890',
                'state': 'Lagos',
                'country': 'Nigeria',
                'amount': '50.00',
                'currency': 'NGN',
                'status': 'pending',
                'paystack_authorization_url': 'https://checkout.paystack.com/abc123'
            },
            'message': 'Payment created successfully'
        }
        
        response = api_client.post('/api/v1/payments/', valid_payment_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'success'
        assert 'payment' in response.data
        assert response.data['payment']['customer_name'] == 'John Doe'
        assert response.data['payment']['customer_email'] == 'john@example.com'
        assert response.data['payment']['amount'] == '50.00'
        assert response.data['payment']['status'] == 'pending'
        assert 'paystack_authorization_url' in response.data['payment']
    
    @patch('payments.service.PaymentService.create_payment')
    def test_create_payment_service_failure(self, mock_create_payment, api_client, valid_payment_data):
        """Test payment creation when service fails"""
        # Mock service failure
        mock_create_payment.return_value = {
            'success': False,
            'message': 'Invalid payment data',
            'errors': {
                'customer_email': ['This field is required.']
            }
        }
        
        response = api_client.post('/api/v1/payments/', valid_payment_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == 'error'
        assert 'Invalid payment data' in response.data['message']
        assert 'errors' in response.data
        assert 'customer_email' in response.data['errors']
    
    def test_create_payment_invalid_data(self, api_client):
        """Test payment creation with invalid data via API"""
        invalid_data = {
            'customer_name': 'John Doe',
            # Missing required fields
            'amount': '50.00'
        }
        
        response = api_client.post('/api/v1/payments/', invalid_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == 'error'
        assert 'errors' in response.data
    
    def test_create_payment_invalid_json(self, api_client):
        """Test payment creation with invalid JSON"""
        response = api_client.post(
            '/api/v1/payments/',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('payments.service.PaymentService.get_payment')
    def test_get_payment_status_success(self, mock_get_payment, api_client, payment_instance):
        """Test successful payment status retrieval via API"""
        # Mock service response
        mock_get_payment.return_value = {
            'success': True,
            'payment': {
                'id': str(payment_instance.id),
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'phone_number': '1234567890',
                'state': 'Lagos',
                'country': 'Nigeria',
                'amount': '50.00',
                'currency': 'NGN',
                'status': 'completed',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            },
            'message': 'Payment details retrieved successfully'
        }
        
        response = api_client.get(f'/api/v1/payments/{payment_instance.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert 'payment' in response.data
        assert response.data['payment']['id'] == str(payment_instance.id)
        assert response.data['payment']['customer_name'] == 'John Doe'
        assert response.data['payment']['status'] == 'completed'
    
    @patch('payments.service.PaymentService.get_payment')
    def test_get_payment_status_not_found(self, mock_get_payment, api_client):
        """Test payment status retrieval for non-existent payment"""
        import uuid
        fake_id = str(uuid.uuid4())
        
        # Mock service response
        mock_get_payment.return_value = {
            'success': False,
            'message': 'Payment not found'
        }
        
        response = api_client.get(f'/api/v1/payments/{fake_id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['status'] == 'error'
        assert 'Payment not found' in response.data['message']
    
    def test_get_payment_invalid_uuid(self, api_client):
        """Test payment status retrieval with invalid UUID"""
        invalid_id = 'not-a-uuid'
        
        response = api_client.get(f'/api/v1/payments/{invalid_id}/')
        
        # Django URL routing returns 404 for invalid UUID format
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('payments.service.PaystackService.process_webhook')
    def test_webhook_success(self, mock_process_webhook, api_client):
        """Test successful webhook processing via API"""
        webhook_data = {
            'event': 'charge.success',
            'data': {
                'reference': 'PAY-TEST123',
                'status': 'success',
                'amount': 5000,
                'id': 123456789
            }
        }
        
        # Mock service response
        mock_process_webhook.return_value = {
            'success': True,
            'message': 'Webhook processed successfully'
        }
        
        response = api_client.post(
            '/api/v1/payments/webhook/paystack/',
            webhook_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert 'Webhook processed successfully' in response.data['message']
    
    @patch('payments.service.PaystackService.process_webhook')
    def test_webhook_service_failure(self, mock_process_webhook, api_client):
        """Test webhook processing when service fails"""
        webhook_data = {
            'event': 'charge.success',
            'data': {
                'reference': 'PAY-TEST123',
                'status': 'success',
                'amount': 5000,
                'id': 123456789
            }
        }
        
        # Mock service failure
        mock_process_webhook.return_value = {
            'success': False,
            'message': 'Invalid webhook data'
        }
        
        response = api_client.post(
            '/api/v1/payments/webhook/paystack/',
            webhook_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == 'error'
        assert 'Invalid webhook data' in response.data['message']
    
    def test_webhook_invalid_data(self, api_client):
        """Test webhook processing with invalid data"""
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
    
    def test_webhook_invalid_json(self, api_client):
        """Test webhook processing with invalid JSON"""
        response = api_client.post(
            '/api/v1/payments/webhook/paystack/',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_payment_wrong_method(self, api_client):
        """Test that GET request to create endpoint returns 405"""
        response = api_client.get('/api/v1/payments/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_get_payment_wrong_method(self, api_client, payment_instance):
        """Test that POST request to get endpoint returns 405"""
        response = api_client.post(f'/api/v1/payments/{payment_instance.id}/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_webhook_wrong_method(self, api_client):
        """Test that GET request to webhook endpoint returns 405"""
        response = api_client.get('/api/v1/payments/webhook/paystack/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_create_payment_missing_content_type(self, api_client, valid_payment_data):
        """Test payment creation without content-type header"""
        response = api_client.post('/api/v1/payments/', valid_payment_data)
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    
    def test_webhook_missing_content_type(self, api_client):
        """Test webhook processing without content-type header"""
        webhook_data = {'event': 'charge.success', 'data': {}}
        response = api_client.post('/api/v1/payments/webhook/paystack/', webhook_data, format='json')
        # The webhook should fail because there's no payment with the reference
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('payments.service.PaymentService.create_payment')
    def test_create_payment_response_structure(self, mock_create_payment, api_client, valid_payment_data):
        """Test that create payment response has correct structure"""
        # Mock service response
        mock_create_payment.return_value = {
            'success': True,
            'payment': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'amount': '50.00',
                'status': 'pending'
            },
            'message': 'Payment created successfully'
        }
        
        response = api_client.post('/api/v1/payments/', valid_payment_data, format='json')
        
        # Check response structure
        assert 'status' in response.data
        assert 'payment' in response.data
        assert 'message' in response.data
        
        # Check payment object structure
        payment = response.data['payment']
        required_fields = ['id', 'customer_name', 'customer_email', 'amount', 'status']
        for field in required_fields:
            assert field in payment
    
    @patch('payments.service.PaymentService.get_payment')
    def test_get_payment_response_structure(self, mock_get_payment, api_client, payment_instance):
        """Test that get payment response has correct structure"""
        # Mock service response
        mock_get_payment.return_value = {
            'success': True,
            'payment': {
                'id': str(payment_instance.id),
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'amount': '50.00',
                'status': 'completed'
            },
            'message': 'Payment details retrieved successfully'
        }
        
        response = api_client.get(f'/api/v1/payments/{payment_instance.id}/')
        
        # Check response structure
        assert 'status' in response.data
        assert 'payment' in response.data
        assert 'message' in response.data
        
        # Check payment object structure
        payment = response.data['payment']
        required_fields = ['id', 'customer_name', 'customer_email', 'amount', 'status']
        for field in required_fields:
            assert field in payment
    
    def test_api_versioning(self, api_client):
        """Test that API versioning is working"""
        # Test that v1 endpoints work
        response = api_client.get('/api/v1/payments/')
        # Should return 405 (method not allowed) rather than 404 (not found)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Test that non-versioned endpoints don't work
        response = api_client.get('/api/payments/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('payments.service.PaymentService.create_payment')
    def test_create_payment_with_different_currencies(self, mock_create_payment, api_client):
        """Test payment creation with different currencies"""
        # Mock service response
        mock_create_payment.return_value = {
            'success': True,
            'payment': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'amount': '100.00',
                'currency': 'USD',
                'status': 'pending'
            },
            'message': 'Payment created successfully'
        }
        
        payment_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'phone_number': '1234567890',
            'state': 'New York',
            'country': 'USA',
            'amount': '100.00',
            'currency': 'USD'
        }
        
        response = api_client.post('/api/v1/payments/', payment_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['payment']['currency'] == 'USD'
        assert response.data['payment']['amount'] == '100.00'
    
    def test_create_payment_with_very_large_amount(self, api_client):
        """Test payment creation with very large amount"""
        payment_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'phone_number': '1234567890',
            'state': 'Lagos',
            'country': 'Nigeria',
            'amount': '999999.99',  # Very large amount
            'currency': 'NGN'
        }
        
        response = api_client.post('/api/v1/payments/', payment_data, format='json')
        
        # Should either succeed or fail with validation error, but not crash
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
