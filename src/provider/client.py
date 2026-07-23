import logging
import httpx

from src.config import config

logger = logging.getLogger(__name__)

class ProviderError(Exception):
    pass

class ProviderClient:
    @staticmethod
    async def send_payment(operation_id: str, amount: str, currency: str = "RUB") -> str:
        url = f"{config.PROVIDER_URL}/payments"

        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": operation_id,
            "X-Correlation-ID": operation_id,
        }

        payload = {
            "operationId": operation_id,
            "amount": amount,
            "currency": currency,
        }

        logger.info(f"Sending payment: {operation_id}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 202:
                    data = response.json()
                    return data["providerPaymentId"]

                elif response.status_code >= 500:
                    raise ProviderError(f"Provider unavailable: {response.status_code}")

                else:
                    raise ProviderError(f"Provider error: {response.status_code}")

        except httpx.TimeoutException:
            raise ProviderError("Provider timeout")

        except httpx.ConnectError:
            raise ProviderError("Provider connection error")