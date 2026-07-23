import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError

from src.storage.database import async_session_maker
from src.storage.models import Operation, Event, OperationStatus

logger = logging.getLogger(__name__)

class OperationRepository:
    @staticmethod
    async def create(operation_data: dict) -> Operation:
        async with async_session_maker() as session:
            operation = Operation(
                operation_id=operation_data["operation_id"],
                amount=operation_data["amount"],
                currency=operation_data.get("currency", "RUB"),
                description=operation_data.get("description", ""),
                status=OperationStatus.CREATED
            )
            session.add(operation)
            try:
                await session.commit()
                await session.refresh(operation)
                return operation
            except IntegrityError:
                await session.rollback()
                raise

    @staticmethod
    async def get_by_id(operation_id: str) -> Optional[Operation]:
        async with async_session_maker() as session:
            query = select(Operation).where(Operation.operation_id == operation_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_provider_payment_id(provider_payment_id: str) -> Optional[Operation]:
        async with async_session_maker() as session:
            query = select(Operation).where(
                Operation.provider_payment_id == provider_payment_id
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_status(
            operation_id: str,
            new_status: OperationStatus,
            message: str = None
    ) -> Optional[Operation]:
        async with async_session_maker() as session:
            query = (
                update(Operation)
                .where(Operation.operation_id == operation_id)
                .values(
                    status=new_status,
                    updated_at=datetime.utcnow()
                )
                .returning(Operation)
            )
            result = await session.execute(query)
            await session.commit()
            return result.scalar_one_or_none()

    @staticmethod
    async def update_status_atomically(
            operation_id: str,
            from_status: OperationStatus,
            to_status: OperationStatus
    ) -> Optional[Operation]:
        async with async_session_maker() as session:
            query = (
                update(Operation)
                .where(
                    and_(
                        Operation.operation_id == operation_id,
                        Operation.status == from_status
                    )
                )
                .values(
                    status=to_status,
                    updated_at=datetime.utcnow()
                )
                .returning(Operation)
            )
            result = await session.execute(query)
            await session.commit()
            return result.scalar_one_or_none()

    @staticmethod
    async def update_provider_payment_id(
            operation_id: str,
            provider_payment_id: str
    ) -> Optional[Operation]:
        async with async_session_maker() as session:
            query = (
                update(Operation)
                .where(Operation.operation_id == operation_id)
                .values(
                    provider_payment_id=provider_payment_id,
                    updated_at=datetime.utcnow()
                )
                .returning(Operation)
            )
            result = await session.execute(query)
            await session.commit()
            return result.scalar_one_or_none()

    @staticmethod
    async def get_all_processing() -> List[Operation]:
        async with async_session_maker() as session:
            query = select(Operation).where(
                Operation.status == OperationStatus.PROCESSING
            )
            result = await session.execute(query)
            return result.scalars().all()



class EventRepository:
    @staticmethod
    async def create_event(
            operation_id: str,
            event_type: str,
            from_status: Optional[str],
            to_status: str,
            message: str = ""
    ) -> Event:
        async with async_session_maker() as session:
            event = Event(
                operation_id=operation_id,
                type=event_type,
                from_status=from_status,
                to_status=to_status,
                message=message,
                occurred_at=datetime.utcnow()
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event

    @staticmethod
    async def get_events_by_operation(operation_id: str) -> List[Event]:
        async with async_session_maker() as session:
            query = (
                select(Event)
                .where(Event.operation_id == operation_id)
                .order_by(Event.event_id.asc())
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_last_event(operation_id: str) -> Optional[Event]:
        async with async_session_maker() as session:
            query = (
                select(Event)
                .where(Event.operation_id == operation_id)
                .order_by(Event.event_id.desc())
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()