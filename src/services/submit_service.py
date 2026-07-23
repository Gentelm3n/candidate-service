import asyncio
import logging
from typing import Dict, Any

from src.storage import OperationRepository, EventRepository
from src.storage.models import OperationStatus
from src.worker import PaymentWorker

logger = logging.getLogger(__name__)


class SubmitService:
    @staticmethod
    async def submit(operation_id: str) -> Dict[str, Any]:
        operation = await OperationRepository.get_by_id(operation_id)
        if not operation:
            raise ValueError(f"Operation {operation_id} not found")

        updated_operation = await OperationRepository.update_status_atomically(
            operation_id=operation_id,
            from_status=OperationStatus.CREATED,
            to_status=OperationStatus.PROCESSING
        )

        if updated_operation:
            logger.info(f"Operation {operation_id} transitioned CREATED → PROCESSING")

            await EventRepository.create_event(
                operation_id=operation_id,
                event_type="PROCESSING",
                from_status=OperationStatus.CREATED.value,
                to_status=OperationStatus.PROCESSING.value,
                message="Submit requested, processing started"
            )

            asyncio.create_task(PaymentWorker.process(operation_id))

            return {
                "is_new": True,
                "status": OperationStatus.PROCESSING.value
            }
        else:
            current = await OperationRepository.get_by_id(operation_id)
            logger.info(f"Operation {operation_id} already in status: {current.status}")

            return {
                "is_new": False,
                "status": current.status.value
            }