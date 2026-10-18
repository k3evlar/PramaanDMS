"""Background worker (Celery with Valkey as the broker).

OCR, Legal Hash and report jobs are added from Phase 6. Phase 3 provides the worker
process, its safe configuration and a `ping` task used by health checks and tests.

Only JSON is accepted for task messages and results, never pickle, so a forged message on
the queue cannot run code (threat T24, ASVS V1.5.2, D60).
"""

from __future__ import annotations

from celery import Celery

from .config import Settings, get_settings
from .logs import configure_logging


def make_celery(settings: Settings) -> Celery:
    url = settings.valkey_url.get_secret_value()
    app = Celery("pramaan", broker=url, backend=url)
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        result_accept_content=["json"],
        enable_utc=True,
        timezone="UTC",
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_time_limit=600,
        task_soft_time_limit=540,
        worker_prefetch_multiplier=1,
        worker_hijack_root_logger=False,
        broker_connection_retry_on_startup=True,
        result_expires=3600,
    )

    @app.task(name="pramaan.ping")
    def ping() -> str:
        return "pong"

    return app


def __getattr__(name: str) -> Celery:
    # `celery -A app.worker.celery_app worker` builds the app on first access.
    if name == "celery_app":
        s = get_settings()
        configure_logging(s.log_level)
        globals()["celery_app"] = make_celery(s)
        return globals()["celery_app"]
    raise AttributeError(name)
