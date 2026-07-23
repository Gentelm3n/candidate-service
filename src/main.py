import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import config
from storage import init_db, close_db
from api.routes import router
from worker import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Service")
    await init_db()
    logger.info("Database initialized")

    scheduler_task = asyncio.create_task(start_scheduler())
    logger.info("Scheduler started")

    logger.info("Service started successfully")

    yield
    logger.info("Shutting down...")

    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

    await close_db()
    logger.info("Shutdown complete")

app = FastAPI(
    title="Payment Processing Service",
    description="Сервис для обработки платежей с идемпотентностью",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.get("/")
async def root():
    return {
        "service": "Payment Processing Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "create_operation": "POST /operations",
            "get_operation": "GET /operations/{id}",
            "get_events": "GET /operations/{id}/events",
            "submit": "POST /operations/{id}/submit",
            "receipts": "POST /receipts"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    logger.info(f"Server will run on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )