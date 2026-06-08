import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import Settings
from app.services.scheduled_email_sync_service import ScheduledEmailSyncService

logger = logging.getLogger(__name__)

SCHEDULED_EMAIL_SYNC_JOB_ID = "background_email_sync"

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler


def create_background_sync_scheduler(settings: Settings) -> AsyncIOScheduler | None:
    if not settings.enable_background_sync:
        logger.info("Background email sync is disabled")
        return None

    service = ScheduledEmailSyncService(settings=settings)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        service.run_scheduled_sync,
        trigger=IntervalTrigger(minutes=settings.background_sync_interval_minutes),
        id=SCHEDULED_EMAIL_SYNC_JOB_ID,
        replace_existing=True,
        max_instances=1,
    )
    return scheduler


def start_background_sync_scheduler(settings: Settings) -> AsyncIOScheduler | None:
    global _scheduler

    if _scheduler is not None:
        return _scheduler

    scheduler = create_background_sync_scheduler(settings)
    if scheduler is None:
        return None

    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Background email sync scheduler started interval_minutes=%s max_results=%s",
        settings.background_sync_interval_minutes,
        settings.background_sync_max_results,
    )
    return scheduler


def shutdown_background_sync_scheduler() -> None:
    global _scheduler

    if _scheduler is None:
        return

    try:
        _scheduler.shutdown(wait=False)
    except RuntimeError:
        logger.debug("Background email sync scheduler shutdown skipped: event loop unavailable")
    _scheduler = None
    logger.info("Background email sync scheduler stopped")
