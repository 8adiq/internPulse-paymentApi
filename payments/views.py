from django.shortcuts import render
from .service import PaymentService,PaystackService
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import uuid

@api_view(['POST'])
def create_payment(request):

    result = PaymentService.create_payment(request.data)

    if result['success']:
        return Response(
            {
                'status':'success',
                'payment':result['payment'],
                'message':result['message']
            },status=status.HTTP_201_CREATED
        )
    return Response({
        'status':'error',
        'message':result['message'],
        'errors': result.get('errors', {})
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_payment_status(request,payment_id):

    # payment_id is already a UUID object from URL routing
    result = PaymentService.get_payment(str(payment_id))

    if result['success']:
        return Response(
            {
                'status':'success',
                'payment':result['payment'],
                'message':result['message']
            },status=status.HTTP_200_OK
        )
    return Response({
        'status':'error',
        'message':result['message'],
        'errors': result.get('errors', {})
    }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def paystack_webhook(request):

    try:
        webhook_data = request.data
        result = PaystackService.process_webhook(webhook_data)

        if result['success']:
            return Response({
                'status': 'success',
                'message': 'Webhook processed successfully'
            },status=status.HTTP_200_OK)
            
        return Response({
            'status': 'error',
            'message': result['message']
        },status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error processing webhook: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)



