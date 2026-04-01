from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import Base, engine, SessionLocal
from app.routers import clients, sessions, invoices, payments, reminders, dashboard, import_export
from app.services.reminder_engine import process_due_reminders, check_overdue_invoices

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_reminder_jobs():
    """Scheduled job: check overdue invoices and process due reminders."""
    db = SessionLocal()
    try:
        overdue = check_overdue_invoices(db)
        sent = process_due_reminders(db)
        if overdue or sent:
            logger.info(f"Scheduler: marked {overdue} overdue, sent {len(sent)} reminders")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(_run_reminder_jobs, "interval", hours=1, id="reminder_check")
    scheduler.start()
    logger.info("APScheduler started — checking reminders every hour")
    yield
    scheduler.shutdown()
    logger.info("APScheduler shut down")


app = FastAPI(title="Invoice Automation", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients.router)
app.include_router(sessions.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(reminders.router)
app.include_router(dashboard.router)
app.include_router(import_export.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
