import asyncio
import logging
import random
from typing import Optional

from src.storage import OperationRepository, EventRepository
from src.storage.models import OperationStatus
from src.provider import ProviderClient, ProviderError

logger = logging.getLogger(__name__)


class PaymentWorker:
    @staticmethod
    async def process(operation_id: str) -> None:
        logger.info(f"Processing operation: {operation_id}")

        operation = await OperationRepository.get_by_id(operation_id)
        if not operation:
            logger.error(f"Operation {operation_id} not found")
            return

        if operation.status in (OperationStatus.COMPLETED, OperationStatus.REJECTED):
            logger.info(f"Operation {operation_id} already finalized: {operation.status}")
            return

        if not operation.provider_payment_id:
            try:
                provider_payment_id = await ProviderClient.send_payment(
                    operation_id=operation.operation_id,
                    amount=str(operation.amount),
                    currency=operation.currency
                )

                await OperationRepository.update_provider_payment_id(
                    operation_id,
                    provider_payment_id
                )

                logger.info(f"Payment sent: {operation_id} → {provider_payment_id}")

            except ProviderError as e:
                logger.warning(f"Provider error for {operation_id}: {e}")
                await PaymentWorker._schedule_retry(operation_id)
                return

            except Exception as e:
                logger.error(f"Unexpected error for {operation_id}: {e}")
                await PaymentWorker._schedule_retry(operation_id)
                return

        else:
            logger.info(f"ℹ️ Operation {operation_id} already has provider_payment_id: {operation.provider_payment_id}")
            # TODO: можно добавить проверку статуса у провайдера

    @staticmethod
    async def _schedule_retry(operation_id: str, delay_seconds: Optional[float] = None) -> None:
        if delay_seconds is None:
            events = await EventRepository.get_events_by_operation(operation_id)
            attempts = len([e for e in events if e.type == "RETRY"])

            base_delay = min(2 ** attempts, 60)
            jitter = random.uniform(0, base_delay * 0.1)
            delay_seconds = base_delay + jitter

        logger.info(f"Retry for {operation_id} in {delay_seconds:.1f}s")

        await EventRepository.create_event(
            operation_id=operation_id,
            event_type="RETRY",
            from_status=None,
            to_status=OperationStatus.PROCESSING.value,
            message=f"Scheduled retry in {delay_seconds:.1f}s"
        )

        asyncio.create_task(PaymentWorker._delayed_retry(operation_id, delay_seconds))

    @staticmethod
    async def _delayed_retry(operation_id: str, delay_seconds: float) -> None:
        await asyncio.sleep(delay_seconds)
        await PaymentWorker.process(operation_id)