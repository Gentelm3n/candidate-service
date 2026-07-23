from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class CreateOperationRequest(BaseModel):
    operationId: str = Field(..., min_length=1, max_length=100)
    amount: str
    currency: str = "RUB"
    description: Optional[str] = ""

    @validator('amount')
    def validate_amount(cls, v):
        try:
            amount_float = float(v)
            if amount_float <= 0:
                raise ValueError("Amount must be positive")
            if len(v.split('.')[-1]) > 2:
                raise ValueError("Amount must have at most 2 decimal places")
            return v
        except ValueError:
            raise ValueError("Amount must be a valid number")

    @validator('currency')
    def validate_currency(cls, v):
        if v != "RUB":
            raise ValueError("Only RUB currency is supported")
        return v


class OperationResponse(BaseModel):
    operationId: str
    amount: str
    currency: str
    description: str
    status: str
    providerPaymentId: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class EventResponse(BaseModel):
    eventId: int
    type: str
    fromStatus: Optional[str] = None
    toStatus: str
    message: str
    occurredAt: datetime


class SubmitResponse(BaseModel):
    operationId: str
    status: str
    message: str


class ReceiptRequest(BaseModel):
    providerPaymentId: str
    operationId: str
    result: str
    message: str
    occurredAt: datetime

    @validator('result')
    def validate_result(cls, v):
        if v not in ["COMPLETED", "REJECTED"]:
            raise ValueError("Result must be COMPLETED or REJECTED")
        return v


class ProviderPaymentRequest(BaseModel):
    operationId: str
    amount: str
    currency: str = "RUB"


class ProviderPaymentResponse(BaseModel):
    providerPaymentId: str
    status: str
