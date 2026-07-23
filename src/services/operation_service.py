import logging
from typing import Optional, List

from sqlalchemy.exc import IntegrityError

from src.storage import OperationRepository, EventRepository
from src.storage.models import Operation, OperationStatus
from src.services.schemas import (
    CreateOperationRequest,
    OperationResponse,
    EventResponse
)

logger = logging.getLogger(__name__)


class OperationService:
    @staticmethod
    async def create(request: CreateOperationRequest) -> OperationResponse:
        try:
            operation = await OperationRepository.create({
                "operation_id": request.operationId,
                "amount": request.amount,
                "currency": request.currency,
                "description": request.description or ""
            })
            await EventRepository.create_event(
                operation_id=request.operationId,
                event_type="CREATED",
                from_status=None,
                to_status=OperationStatus.CREATED.value,
                message="Operation created"
            )

            logger.info(f"Operation {request.operationId} created successfully")

            return OperationService._to_response(operation)

        except IntegrityError:
            logger.warning(f"Duplicate operation {request.operationId} creation attempt")
            raise

    @staticmethod
    async def get_by_id(operation_id: str) -> Optional[OperationResponse]:
        operation = await OperationRepository.get_by_id(operation_id)
        if not operation:
            return None
        return OperationService._to_response(operation)

    @staticmethod
    async def get_events(operation_id: str) -> List[EventResponse]:
        events = await EventRepository.get_events_by_operation(operation_id)
        return [
            EventResponse(
                eventId=event.event_id,
                type=event.type,
                fromStatus=event.from_status,
                toStatus=event.to_status,
                message=event.message,
                occurredAt=event.occurred_at
            )
            for event in events
        ]

    @staticmethod
    def _to_response(operation: Operation) -> OperationResponse:
        return OperationResponse(
            operationId=operation.operation_id,
            amount=str(operation.amount),
            currency=operation.currency,
            description=operation.description or "",
            status=operation.status.value,
            providerPaymentId=operation.provider_payment_id,
            createdAt=operation.created_at,
            updatedAt=operation.updated_at
        )