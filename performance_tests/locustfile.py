from locust import HttpUser, task, between
import json
import uuid

class PaymentAPIUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize user session"""
        self.base_url = "/api/v1/payments"
        
    @task(3)
    def create_payment(self):
        """Test payment creation endpoint"""
        payment_data = {
            "customer_name": f"Test User {uuid.uuid4().hex[:8]}",
            "customer_email": f"test{uuid.uuid4().hex[:8]}@example.com",
            "phone_number": "1234567890",
            "state": "Lagos",
            "country": "Nigeria",
            "amount": "50.00",
            "currency": "NGN"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        with self.client.post(
            self.base_url + "/",
            json=payment_data,
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
                # Store payment ID for status check
                try:
                    payment_id = response.json().get("payment", {}).get("id")
                    if payment_id:
                        self.payment_id = payment_id
                except:
                    pass
            else:
                response.failure(f"Expected 201, got {response.status_code}")
    
    @task(2)
    def get_payment_status(self):
        """Test payment status retrieval endpoint"""
        # Use stored payment ID or generate a fake one
        payment_id = getattr(self, 'payment_id', str(uuid.uuid4()))
        
        with self.client.get(
            f"{self.base_url}/{payment_id}/",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Expected 200 or 404, got {response.status_code}")
    
    @task(1)
    def test_webhook_endpoint(self):
        """Test webhook endpoint"""
        webhook_data = {
            "event": "charge.success",
            "data": {
                "reference": f"PAY-{uuid.uuid4().hex[:8].upper()}",
                "status": "success",
                "amount": 5000,
                "id": 123456789
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        with self.client.post(
            self.base_url + "/webhook/paystack/",
            json=webhook_data,
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 400]:
                response.success()
            else:
                response.failure(f"Expected 200 or 400, got {response.status_code}")
    
    @task(1)
    def test_invalid_payment_creation(self):
        """Test payment creation with invalid data"""
        invalid_data = {
            "customer_name": "Test User",
            # Missing required fields
            "amount": "50.00"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        with self.client.post(
            self.base_url + "/",
            json=invalid_data,
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(f"Expected 400, got {response.status_code}")
    
    @task(1)
    def test_invalid_uuid(self):
        """Test payment status with invalid UUID"""
        invalid_id = "not-a-uuid"
        
        with self.client.get(
            f"{self.base_url}/{invalid_id}/",
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Expected 404, got {response.status_code}")

class HighLoadUser(PaymentAPIUser):
    """High load user for stress testing"""
    wait_time = between(0.5, 1.5)  # Faster requests
    
    @task(5)
    def rapid_payment_creation(self):
        """Rapid payment creation for stress testing"""
        self.create_payment()
    
    @task(3)
    def rapid_status_checks(self):
        """Rapid status checks for stress testing"""
        self.get_payment_status()
