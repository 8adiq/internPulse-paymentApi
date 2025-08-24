#!/usr/bin/env python3
"""
Test script for Payment API endpoints
"""
import requests
import json
import uuid

# API Base URL
BASE_URL = "http://127.0.0.1:8000/api/v1/payments"

def test_create_payment():
    """Test creating a payment"""
    print("🧪 Testing: Create Payment")
    print("=" * 50)
    
    # Test data
    payment_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "phone_number": "1234567890",
        "state": "Lagos",
        "country": "Nigeria",
        "amount": "50.00",
        "currency": "NGN"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/",
            json=payment_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Create Payment: SUCCESS")
            return response.json().get('payment', {}).get('id')
        else:
            print("❌ Create Payment: FAILED")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_get_payment_status(payment_id):
    """Test getting payment status"""
    print("\n🧪 Testing: Get Payment Status")
    print("=" * 50)
    
    if not payment_id:
        print("❌ No payment ID available")
        return
    
    try:
        response = requests.get(f"{BASE_URL}/{payment_id}/")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get Payment Status: SUCCESS")
        else:
            print("❌ Get Payment Status: FAILED")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_get_nonexistent_payment():
    """Test getting a payment that doesn't exist"""
    print("\n🧪 Testing: Get Non-existent Payment")
    print("=" * 50)
    
    fake_id = str(uuid.uuid4())
    
    try:
        response = requests.get(f"{BASE_URL}/{fake_id}/")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 404:
            print("✅ Get Non-existent Payment: SUCCESS (Correctly returned 404)")
        else:
            print("❌ Get Non-existent Payment: FAILED (Should return 404)")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_invalid_payment_data():
    """Test creating payment with invalid data"""
    print("\n🧪 Testing: Create Payment with Invalid Data")
    print("=" * 50)
    
    # Invalid data (missing required fields)
    invalid_data = {
        "customer_name": "John Doe",
        # Missing email, phone, etc.
        "amount": "50.00"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✅ Invalid Payment Data: SUCCESS (Correctly returned 400)")
        else:
            print("❌ Invalid Payment Data: FAILED (Should return 400)")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_webhook():
    """Test webhook endpoint"""
    print("\n🧪 Testing: Webhook Endpoint")
    print("=" * 50)
    
    # Sample webhook data
    webhook_data = {
        "event": "charge.success",
        "data": {
            "id": 123456789,
            "status": "success",
            "reference": "PAY-TEST123",
            "amount": 5000
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/paystack/",
            json=webhook_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Webhook: SUCCESS")
        else:
            print("❌ Webhook: FAILED")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Starting Payment API Tests")
    print("=" * 60)
    
    # Test 1: Create Payment
    payment_id = test_create_payment()
    
    # Test 2: Get Payment Status
    test_get_payment_status(payment_id)
    
    # Test 3: Get Non-existent Payment
    test_get_nonexistent_payment()
    
    # Test 4: Invalid Payment Data
    test_invalid_payment_data()
    
    # Test 5: Webhook
    test_webhook()
    
    print("\n" + "=" * 60)
    print("🏁 Testing Complete!")

if __name__ == "__main__":
    main()
