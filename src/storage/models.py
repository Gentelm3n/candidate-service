from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
import enum
from src.storage.database import Base

class OperationStatus(str, enum.Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

class Operation(Base):
    __tablename__ = "operations"

    operation_id = Column(String(100), primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="RUB")
    description = Column(String(255))
    status = Column(Enum(OperationStatus), nullable=False, default=OperationStatus.CREATED)

    provider_payment_id = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    events = relationship("Event", back_populates="operation", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(String(100), ForeignKey("operations.operation_id"), nullable=False)

    type = Column(String(50), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    message = Column(String(255))

    occurred_at = Column(DateTime, default=datetime.utcnow)

    operation = relationship("Operation", back_populates="events")