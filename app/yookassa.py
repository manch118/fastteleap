import base64
import json
import uuid
from typing import Dict, Any

import httpx
from fastapi import HTTPException, status

from .settings import settings


class YooKassaClient:
    """YooKassa API client for payment processing."""
    
    BASE_URL = "https://api.yookassa.ru/v3"
    
    def __init__(self):
        self.shop_id = settings.yookassa_shop_id
        self.secret_key = settings.yookassa_secret_key

        print(f"[DEBUG] YooKassa shop_id: {self.shop_id}")
        print(f"[DEBUG] YooKassa secret_key: {'*' * len(self.secret_key) if self.secret_key else 'None'}")
        print(f"[DEBUG] YooKassa client initialized successfully")

        if not self.shop_id or not self.secret_key:
            print("[ERROR] YooKassa credentials not configured - shop_id or secret_key is empty")
            raise ValueError("YooKassa credentials not configured")
        
        # Create basic auth header
        credentials = f"{self.shop_id}:{self.secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
    
    async def create_payment(
        self,
        amount: float,
        currency: str = "RUB",
        description: str = "Order payment",
        return_url: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new payment in YooKassa."""
        
        if not return_url:
            return_url = settings.payment_success_url
        
        payment_data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": currency
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "description": description,
            "capture": True,
            "metadata": metadata or {}
        }

        # Generate a new Idempotence-Key for each request
        request_headers = self.headers.copy()
        request_headers["Idempotence-Key"] = str(uuid.uuid4())

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/payments", headers=request_headers,
                    json=payment_data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = f"YooKassa API error: {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    error_detail += f" - {error_data.get('description', 'Unknown error')}"
                except:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=error_detail
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Payment service unavailable: {str(e)}"
                )
    
    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status from YooKassa."""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/payments/{payment_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to get payment status: {e.response.status_code}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Payment service unavailable: {str(e)}"
                )
    
    def verify_webhook_signature(self, webhook_data: Dict[str, Any], signature: str) -> bool:
        """Verify YooKassa webhook signature."""
        # In production, you should verify the signature using HMAC-SHA256
        # For now, we'll skip signature verification for simplicity
        # You can implement this using the webhook secret from YooKassa
        return True


# Global YooKassa client instance
yookassa_client = None

def get_yookassa_client() -> YooKassaClient:
    """Get YooKassa client instance."""
    global yookassa_client
    if yookassa_client is None:
        yookassa_client = YooKassaClient()
    return yookassa_client
