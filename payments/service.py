from .models import Payment
from .serializers import PaymentCreateSerializer,PaymentDetailsSerializer,PaymentStatusSerializer
from decimal import Decimal
from django.db import transaction
import uuid
import requests
from django.conf import settings



class PaymentService:
    """service class for payment related business logic"""

    @staticmethod
    def generate_payment_reference():
        """generate a unique payment reference"""
        return f"PAY-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def create_payment(payment_data):
        """create a payment transaction"""

        try:
            serializer = PaymentCreateSerializer(data=payment_data)
            if not serializer.is_valid():
                return{
                    'success': False,
                    'message': 'Invalid payment data',
                    'errors': serializer.errors
                }

            validated_data = serializer.validated_data
            
            payment_reference = PaymentService.generate_payment_reference()

            with transaction.atomic():
                payment = Payment.objects.create(
                    customer_name=validated_data['customer_name'],
                    customer_email=validated_data['customer_email'],
                    phone_number=validated_data['phone_number'],
                    state=validated_data['state'],
                    country=validated_data['country'],
                    amount=validated_data['amount'],
                    currency=validated_data['currency'],
                    paystack_reference=payment_reference,
                    status='pending'
                )

                paystack_transaction = PaystackService.initiate_payment(payment)

                if paystack_transaction['success']:
                    payment.paystack_authorization_url = paystack_transaction['authorization_url']
                    payment.save()
                    
                    response_serializer = PaymentDetailsSerializer(payment)
                    return {
                        'success': True,
                        'message': 'Payment created successfully',
                        'payment': response_serializer.data
                    }
                else:
                    # If Paystack fails, return the error
                    return {
                        'success': False,
                        'message': paystack_transaction['message'],
                        'errors': paystack_transaction.get('errors', {})
                    }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating payment {str(e)}',
                'errors': {}
            }
            
    @staticmethod
    def get_payment(payment_id):
        """get details of a payment"""

        try:
            payment = Payment.objects.get(id=payment_id)
            serializer = PaymentDetailsSerializer(payment)

            return {
                'success': True,
                'message': 'Payment details retrieved successfully',
                'payment': serializer.data
            }
        except Payment.DoesNotExist:
            return {
                'success':  False,
                'message': 'Payment not found.',
                'errors': {}
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving payment {str(e)}',
                'errors': {}
            }


    @staticmethod
    def update_payment_status(payment_id,new_status):
        """update payment status"""

        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = new_status
            payment.save()

            return {
                'success': True,
                'message': f'Payment status updated {new_status}',
                'payment_id': str(payment_id) 
            }
            
        except Payment.DoesNotExist:
            return {
                'success': False,
                'message': 'Payment not found',
                'errors': {}
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving payment {str(e)}',
                'errors': {}
            }
        
class PaystackService:
    """Service class for paystack payment gateway integration"""

    @staticmethod
    def get_headers():
        """getting headers for paystack api request"""
        return {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
    @staticmethod
    def initiate_payment(payment):
        """initiate a paystack payment"""

        try:
            # preparing payload for paystack
            payload = {
                'amount': int(payment.amount * 100),  # Convert to kobo (smallest currency unit)
                'email': payment.customer_email,
                'reference': payment.paystack_reference,
                'callback_url': f"{settings.BASE_URL}/api/v1/payments/webhook/paystack/",
                'metadata': {
                    'customer_name': payment.customer_name,
                    'phone_number': payment.phone_number,
                    'state': payment.state,
                    'country': payment.country,
                    'payment_id': str(payment.id)
                  }
            }
            # request to paystack
            response = requests.post(
                settings.PAYSTACK_INITIALIZE_URL,
                headers=PaystackService.get_headers(),
                json=payload,
                timeout=30
            )
        
            response_data = response.json()

            if response.status_code == 200  and response_data.get('status'):

                payment.paystack_authorization_url = response_data['data']['authorization_url']
                payment.save()

                return {
                    'success': True,
                    'authorization_url': response_data['data']['authorization_url'],
                    'reference':payment.paystack_reference,
                    'access_code':response_data['data']['access_code'],
                    'message': 'Payment initiated successfully'
                }
            else:
                return {
                'success': False,
                'message': response_data.get('message', 'Failed to initialize payment'),
                'errors': response_data.get('errors', {})
            }

        except requests.exceptions.RequestException as e:
            return {
                'success':  False,
                'message': f'Network error: {str(e)}',
                'errors': {}
            }
        
        except Exception as e:
            return{
                'success':  False,
                'message': f'Error initializing payment: {str(e)}',
                'errors': {}
            }
        
    @staticmethod
    def process_webhook(webhook_data):

        try:

            event = webhook_data.get('event')
            data = webhook_data.get('data',{})

            if event == 'charge.success':

                reference = data.get('reference')
                transaction_id = data.get('id') 

                try:
                    payment = Payment.objects.get(paystack_reference=reference)

                    payment.status = 'completed'
                    payment.paystack_transaction_id = transaction_id
                    payment.save()

                    return {
                        'success': True,
                        'message': 'Payment processed successfully',
                        'payment_id': str(payment.id),
                        'status': 'completed'
                    }
                except Payment.DoesNotExist:
                    return {
                        'success': False,
                        'message': f'Payment with reference {reference} not found',
                        'errors': {}
                    }
            
            elif event == 'charge.failed':

                reference = data.get('reference')
                # transaction_id = data.get('transaction_id')

                try:

                    payment = Payment.objects.get(paystack_reference=reference)

                    payment.status = 'failed'
                    payment.save()

                    return{
                        'success': True,
                        'message': 'Payment marked as failed',
                        'payment_id': str(payment.id),
                        'status': 'failed'
                    }
                except Payment.DoesNotExist:
                    return {
                        'success': False,
                        'message': f'Payment with reference {reference} not found',
                        'errors': {}
                    }
                
            else:
                return {
                'success': False,
                'message': f'Unhandled webhook event: {event}',
                'errors': {}
            }

        except Exception as e:
            return {
            'success': False,
            'message': f'Error processing webhook: {str(e)}',
            'errors': {}
        }






    



            

