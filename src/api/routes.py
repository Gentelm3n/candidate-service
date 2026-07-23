import logging
from fastapi import APIRouter, HTTPException, status
from src.services import OperationService, ReceiptService
from src.services.schemas import CreateOperationRequest, OperationResponse, EventResponse, ReceiptRequest
from src.services.submit_service import SubmitService
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "message": "Service is running"}


@router.post("/operations", status_code=status.HTTP_201_CREATED)
async def create_operation(request: CreateOperationRequest):
    logger.info("POST OPERATION CREATED")
    try:
        result = await OperationService.create(request)
        logger.info("POST OPERATION CREATED 1")
        return result
    except Exception as e:
        if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Operation {request.operationId} already exists"
            )
        logger.error(f"Error creating operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/operations/{operation_id}")
async def get_operation(operation_id: str):
    result = await OperationService.get_by_id(operation_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation {operation_id} not found"
        )
    return result


@router.get("/operations/{operation_id}/events")
async def get_events(operation_id: str):
    operation = await OperationService.get_by_id(operation_id)
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation {operation_id} not found"
        )
    events = await OperationService.get_events(operation_id)
    return events


@router.post("/operations/{operation_id}/submit")
async def submit_operation(operation_id: str):
    result = await SubmitService.submit(operation_id)

    if result["status"] == "PROCESSING" and result.get("is_new"):
        return {"operationId": operation_id, "status": "PROCESSING", "message": "Accepted"}, 202
    else:
        return {"operationId": operation_id, "status": result["status"], "message": "Already processing"}, 200


@router.post("/receipts", status_code=status.HTTP_204_NO_CONTENT)
async def handle_receipt(receipt: ReceiptRequest):
    try:
        await ReceiptService.process(receipt)
        return None
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "mismatch" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Receipt processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/")
async def root():
    return {
        "service": "Payment Processing Service",
        "version": "1.0.0",
        "docs": "/docs"
    }


@router.get("/db-test")
async def db_test():
    try:
        from src.storage.database import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}