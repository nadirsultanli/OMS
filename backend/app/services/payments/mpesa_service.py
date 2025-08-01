"""
M-PESA Service for handling mobile money payments
"""

import base64
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
import requests
from requests.auth import HTTPBasicAuth

from app.core.config import settings
from app.infrastucture.logs.logger import get_logger

logger = get_logger("mpesa_service")


class MpesaService:
    """M-PESA payment service for mobile money transactions"""
    
    def __init__(self):
        self.consumer_key = settings.mpesa_consumer_key
        self.consumer_secret = settings.mpesa_consumer_secret
        self.shortcode = settings.mpesa_shortcode or "174379"  # Default sandbox shortcode
        self.passkey = settings.mpesa_passkey or "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        self.environment = settings.mpesa_environment or "sandbox"  # sandbox or production
        
        # Base URLs
        if self.environment == "production":
            self.base_url = "https://api.safaricom.co.ke"
        else:
            self.base_url = "https://sandbox.safaricom.co.ke"
        
        self.access_token = None
        self.token_expiry = None
    
    async def get_access_token(self) -> str:
        """Get M-PESA access token"""
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
                return self.access_token
            
            # Get new token
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get M-PESA access token: {response.status_code} - {response.text}")
                raise Exception(f"M-PESA authentication failed: {response.status_code}")
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            # Set expiry (tokens typically last 1 hour)
            from datetime import timedelta
            self.token_expiry = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=55)  # 5 min buffer
            
            logger.info("M-PESA access token obtained successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Error getting M-PESA access token: {str(e)}")
            raise Exception(f"Failed to authenticate with M-PESA: {str(e)}")
    
    def generate_password(self, shortcode: str, passkey: str, timestamp: str) -> str:
        """Generate M-PESA API password"""
        try:
            # Concatenate shortcode, passkey, and timestamp
            string_to_encode = f"{shortcode}{passkey}{timestamp}"
            
            # Encode to base64
            encoded_string = base64.b64encode(string_to_encode.encode()).decode()
            
            return encoded_string
            
        except Exception as e:
            logger.error(f"Error generating M-PESA password: {str(e)}")
            raise Exception(f"Failed to generate M-PESA password: {str(e)}")
    
    def generate_timestamp(self) -> str:
        """Generate timestamp in M-PESA format (YYYYMMDDHHMMSS)"""
        return datetime.now().strftime('%Y%m%d%H%M%S')
    
    async def initiate_stk_push(
        self,
        phone_number: str,
        amount: Decimal,
        reference: str,
        description: str = "Payment"
    ) -> Dict[str, Any]:
        """Initiate STK Push for payment"""
        try:
            # Get access token
            access_token = await self.get_access_token()
            
            # Generate timestamp and password
            timestamp = self.generate_timestamp()
            password = self.generate_password(self.shortcode, self.passkey, timestamp)
            
            # Format phone number (remove + and add 254 if needed)
            formatted_phone = self.format_phone_number(phone_number)
            
            # Prepare request payload
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),  # M-PESA expects integer amount
                "PartyA": formatted_phone,
                "PartyB": self.shortcode,
                "PhoneNumber": formatted_phone,
                "CallBackURL": "https://aware-endurance-production.up.railway.app/api/v1/payments/mpesa/callback",
                "AccountReference": reference,
                "TransactionDesc": description
            }
            
            # Make API call
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Initiating M-PESA STK Push for {formatted_phone}, amount: {amount}")
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"M-PESA STK Push failed: {response.status_code} - {response.text}")
                raise Exception(f"M-PESA STK Push failed: {response.status_code}")
            
            result = response.json()
            
            # Log the response
            logger.info(f"M-PESA STK Push initiated successfully: {result.get('CheckoutRequestID')}")
            
            return {
                'success': True,
                'checkout_request_id': result.get('CheckoutRequestID'),
                'merchant_request_id': result.get('MerchantRequestID'),
                'response_code': result.get('ResponseCode'),
                'response_description': result.get('ResponseDescription'),
                'customer_message': result.get('CustomerMessage'),
                'timestamp': timestamp,
                'phone_number': formatted_phone
            }
            
        except Exception as e:
            logger.error(f"Error initiating M-PESA STK Push: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'checkout_request_id': None,
                'merchant_request_id': None
            }
    
    async def check_transaction_status(self, checkout_request_id: str) -> Dict[str, Any]:
        """Check transaction status using CheckoutRequestID"""
        try:
            # Get access token
            access_token = await self.get_access_token()
            
            # Generate timestamp and password
            timestamp = self.generate_timestamp()
            password = self.generate_password(self.shortcode, self.passkey, timestamp)
            
            # Prepare request payload
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            # Make API call
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Checking M-PESA transaction status for: {checkout_request_id}")
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"M-PESA status check failed: {response.status_code} - {response.text}")
                raise Exception(f"M-PESA status check failed: {response.status_code}")
            
            result = response.json()
            
            logger.info(f"M-PESA status check result: {result.get('ResultCode')}")
            
            return {
                'success': True,
                'result_code': result.get('ResultCode'),
                'result_description': result.get('ResultDesc'),
                'checkout_request_id': result.get('CheckoutRequestID'),
                'merchant_request_id': result.get('MerchantRequestID'),
                'amount': result.get('Amount'),
                'mpesa_receipt_number': result.get('MpesaReceiptNumber'),
                'transaction_date': result.get('TransactionDate'),
                'phone_number': result.get('PhoneNumber')
            }
            
        except Exception as e:
            logger.error(f"Error checking M-PESA transaction status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'result_code': None,
                'result_description': None
            }
    
    def format_phone_number(self, phone_number: str) -> str:
        """Format phone number for M-PESA API"""
        try:
            # Remove all non-digit characters
            digits_only = ''.join(filter(str.isdigit, phone_number))
            
            # Handle different formats
            if digits_only.startswith('254'):
                return digits_only
            elif digits_only.startswith('0'):
                return '254' + digits_only[1:]
            elif digits_only.startswith('7'):
                return '254' + digits_only
            elif len(digits_only) == 9:
                return '254' + digits_only
            else:
                # Assume it's already in correct format
                return digits_only
                
        except Exception as e:
            logger.error(f"Error formatting phone number {phone_number}: {str(e)}")
            return phone_number
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        try:
            formatted = self.format_phone_number(phone_number)
            # M-PESA expects 12 digits starting with 254
            return len(formatted) == 12 and formatted.startswith('254')
        except:
            return False
    
    async def process_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process M-PESA callback data"""
        try:
            logger.info(f"Processing M-PESA callback: {callback_data}")
            
            # Extract relevant information
            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_description = stk_callback.get('ResultDesc')
            
            # Check if payment was successful
            if result_code == 0:
                # Payment successful
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                item_list = callback_metadata.get('Item', [])
                
                # Extract payment details
                payment_data = {}
                for item in item_list:
                    name = item.get('Name')
                    value = item.get('Value')
                    if name and value is not None:
                        payment_data[name] = value
                
                return {
                    'success': True,
                    'checkout_request_id': checkout_request_id,
                    'result_code': result_code,
                    'result_description': result_description,
                    'mpesa_receipt_number': payment_data.get('MpesaReceiptNumber'),
                    'transaction_date': payment_data.get('TransactionDate'),
                    'amount': payment_data.get('Amount'),
                    'phone_number': payment_data.get('PhoneNumber'),
                    'merchant_request_id': payment_data.get('MerchantRequestID')
                }
            else:
                # Payment failed
                return {
                    'success': False,
                    'checkout_request_id': checkout_request_id,
                    'result_code': result_code,
                    'result_description': result_description,
                    'error': f"Payment failed: {result_description}"
                }
                
        except Exception as e:
            logger.error(f"Error processing M-PESA callback: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'checkout_request_id': None,
                'result_code': None
            }
    
    async def refund_payment(
        self,
        transaction_id: str,
        amount: Decimal,
        phone_number: str,
        reference: str
    ) -> Dict[str, Any]:
        """Refund a payment (B2C API)"""
        try:
            # Get access token
            access_token = await self.get_access_token()
            
            # Generate timestamp and password
            timestamp = self.generate_timestamp()
            password = self.generate_password(self.shortcode, self.passkey, timestamp)
            
            # Format phone number
            formatted_phone = self.format_phone_number(phone_number)
            
            # Prepare request payload
            payload = {
                "InitiatorName": "testapi",  # This should be configurable
                "SecurityCredential": password,
                "CommandID": "BusinessPayment",
                "Amount": int(amount),
                "PartyA": self.shortcode,
                "PartyB": formatted_phone,
                "Remarks": f"Refund for {reference}",
                "QueueTimeOutURL": f"{settings.backend_url}/api/v1/payments/mpesa/timeout",
                "ResultURL": f"{settings.backend_url}/api/v1/payments/mpesa/result",
                "Occasion": reference
            }
            
            # Make API call
            url = f"{self.base_url}/mpesa/b2c/v1/paymentrequest"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Initiating M-PESA refund for {formatted_phone}, amount: {amount}")
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"M-PESA refund failed: {response.status_code} - {response.text}")
                raise Exception(f"M-PESA refund failed: {response.status_code}")
            
            result = response.json()
            
            logger.info(f"M-PESA refund initiated successfully: {result.get('ConversationID')}")
            
            return {
                'success': True,
                'conversation_id': result.get('ConversationID'),
                'originator_conversation_id': result.get('OriginatorConversationID'),
                'response_code': result.get('ResponseCode'),
                'response_description': result.get('ResponseDescription')
            }
            
        except Exception as e:
            logger.error(f"Error initiating M-PESA refund: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'conversation_id': None,
                'originator_conversation_id': None
            } 