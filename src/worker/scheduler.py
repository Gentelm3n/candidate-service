import asyncio
import logging

from src.storage import OperationRepository
from src.worker.payment_worker import PaymentWorker

logger = logging.getLogger(__name__)


async def start_scheduler() -> None:
    logger.info("Scheduler started")

    while True:
        try:
            processing_operations = await OperationRepository.get_all_processing()

            if processing_operations:
                logger.info(f"Found {len(processing_operations)} operations in PROCESSING state")

                for operation in processing_operations:
                    logger.info(f"Resuming operation: {operation.operation_id}")
                    asyncio.create_task(PaymentWorker.process(operation.operation_id))
            else:
                logger.debug("No PROCESSING operations found")

        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        from src.config import config
        await asyncio.sleep(config.SCHEDULER_INTERVAL)