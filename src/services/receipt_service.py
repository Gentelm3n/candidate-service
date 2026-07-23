import logging
from typing import Optional
from src.storage import OperationRepository, EventRepository
from src.storage.models import OperationStatus
from src.services.schemas import ReceiptRequest

logger = logging.getLogger(__name__)


class ReceiptService:
    @staticmethod
    async def process(receipt: ReceiptRequest) -> None:
        logger.info(f"Processing receipt: operation_id={receipt.operationId}, result={receipt.result}")

        operation = await OperationRepository.get_by_id(receipt.operationId)
        if not operation:
            logger.error(f"Operation {receipt.operationId} not found")
            raise ValueError(f"Operation {receipt.operationId} not found")

        if operation.provider_payment_id and operation.provider_payment_id != receipt.providerPaymentId:
            logger.error(
                f"ProviderPaymentId mismatch: {operation.provider_payment_id} vs {receipt.providerPaymentId}")
            raise ValueError("ProviderPaymentId mismatch")

        if not operation.provider_payment_id:
            await OperationRepository.update_provider_payment_id(
                receipt.operationId,
                receipt.providerPaymentId
            )
            logger.info(f"Saved providerPaymentId: {receipt.providerPaymentId}")

        if operation.status in (OperationStatus.COMPLETED, OperationStatus.REJECTED):
            logger.info(f"Operation {receipt.operationId} already finalized: {operation.status}")
            return

        new_status = OperationStatus.COMPLETED if receipt.result == "COMPLETED" else OperationStatus.REJECTED

        updated = await OperationRepository.update_status(
            receipt.operationId,
            new_status
        )

        if updated:
            await EventRepository.create_event(
                operation_id=receipt.operationId,
                event_type=new_status.value,
                from_status=OperationStatus.PROCESSING.value,
                to_status=new_status.value,
                message=f"Provider callback: {receipt.message}"
            )
            logger.info(f"Operation {receipt.operationId} → {new_status.value}")
        else:
            logger.error(f"Failed to update status for {receipt.operationId}")