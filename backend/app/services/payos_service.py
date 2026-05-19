"""PayOS Integration for Subscription Payments"""
import hashlib
import hmac
import json
import time
from typing import Optional
import httpx
from app.core.config import settings


class PayOSService:
    """PayOS payment gateway integration"""

    def __init__(self):
        self.client_id = settings.PAYOS_CLIENT_ID
        self.api_key = settings.PAYOS_API_KEY
        self.checksum_key = settings.PAYOS_CHECKSUM_KEY
        self.base_url = "https://api-merchant.payos.vn/v2"

    def create_payment_link(
        self,
        order_code: int,
        amount: int,
        description: str,
        return_url: str,
        cancel_url: str,
        buyer_name: Optional[str] = None,
        buyer_email: Optional[str] = None,
        buyer_phone: Optional[str] = None,
    ) -> dict:
        """
        Create PayOS payment link

        Args:
            order_code: Unique order code (integer)
            amount: Amount in VND
            description: Payment description
            return_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            buyer_name: Optional buyer name
            buyer_email: Optional buyer email
            buyer_phone: Optional buyer phone

        Returns:
            dict with payment_url and other info
        """
        # Prepare data
        data = {
            "orderCode": order_code,
            "amount": amount,
            "description": description,
            "returnUrl": return_url,
            "cancelUrl": cancel_url,
            "items": [
                {
                    "name": description,
                    "quantity": 1,
                    "price": amount
                }
            ]
        }

        # Add buyer info if provided
        if buyer_name or buyer_email or buyer_phone:
            data["buyerName"] = buyer_name or ""
            data["buyerEmail"] = buyer_email or ""
            data["buyerPhone"] = buyer_phone or ""

        # Debug: Print request data
        print(f"PayOS Request Data: {data}")

        # Make API request
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        print(f"PayOS Headers: x-client-id={self.client_id[:10]}..., x-api-key={self.api_key[:10]}...")

        try:
            response = httpx.post(
                f"{self.base_url}/payment-requests",
                json=data,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

            return {
                "success": True,
                "payment_url": result.get("checkoutUrl"),
                "order_code": order_code,
                "qr_code": result.get("qrCode"),
                "data": result,
            }
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            print(f"PayOS HTTP Error: {e.response.status_code} - {error_detail}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {error_detail}",
            }
        except Exception as e:
            print(f"PayOS Error: {type(e).__name__} - {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    def verify_webhook_signature(self, webhook_data: dict, signature: str) -> bool:
        """
        Verify PayOS webhook signature

        Args:
            webhook_data: Webhook data from PayOS
            signature: Signature from webhook header

        Returns:
            bool: True if signature is valid
        """
        # Sort data keys
        sorted_data = "&".join(
            f"{k}={v}" for k, v in sorted(webhook_data.items())
        )

        # Create HMAC signature
        expected_signature = hmac.new(
            self.checksum_key.encode(),
            sorted_data.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def get_payment_info(self, order_code: int) -> dict:
        """
        Get payment information by order code

        Args:
            order_code: Order code

        Returns:
            dict with payment info
        """
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key,
        }

        try:
            response = httpx.get(
                f"{self.base_url}/payment-requests/{order_code}",
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def cancel_payment(self, order_code: int, reason: Optional[str] = None) -> dict:
        """
        Cancel a payment

        Args:
            order_code: Order code
            reason: Optional cancellation reason

        Returns:
            dict with result
        """
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        data = {}
        if reason:
            data["cancellationReason"] = reason

        try:
            response = httpx.post(
                f"{self.base_url}/payment-requests/{order_code}/cancel",
                json=data,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _create_signature(self, data: dict) -> str:
        """Create signature for payment request"""
        # Sort data by keys
        sorted_data = "&".join(
            f"{k}={v}" for k, v in sorted(data.items())
        )

        # Create HMAC SHA256 signature
        signature = hmac.new(
            self.checksum_key.encode(),
            sorted_data.encode(),
            hashlib.sha256,
        ).hexdigest()

        return signature


# Singleton instance
payos_service = PayOSService()
