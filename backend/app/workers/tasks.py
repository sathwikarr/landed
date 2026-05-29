"""Celery tasks — wraps async pipeline for background execution."""
import asyncio
from celery import Celery
import os
import json
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("jobapply", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])

_redis = redis.from_url(REDIS_URL)


def _publish(run_id: str, event: dict):
    _redis.publish(f"run:{run_id}", json.dumps(event))


@celery_app.task(bind=True, name="tasks.run_pipeline")
def run_pipeline_task(self, run_id: str, user_id: str, profile_data: dict, prefs_data: dict, resume_text: str):
    from app.models.schemas import RunSession, UserProfile, UserPreferences, RunStatus
    from app.agents.orchestrator import run_pipeline
    from datetime import datetime

    run = RunSession(id=run_id, user_id=user_id, status=RunStatus.running, started_at=datetime.utcnow())
    profile = UserProfile(**profile_data)
    prefs = UserPreferences(**prefs_data)

    async def progress_callback(event: dict):
        event["run_id"] = run_id
        _publish(run_id, event)

    async def _run():
        return await run_pipeline(run, profile, prefs, resume_text, progress_callback)

    final_run, applications = asyncio.run(_run())

    # Publish completion
    _publish(run_id, {
        "event": "complete",
        "run_id": run_id,
        "apps_submitted": final_run.apps_submitted,
        "apps_flagged": final_run.apps_flagged,
    })

    return {
        "run_id": run_id,
        "status": final_run.status,
        "apps_submitted": final_run.apps_submitted,
        "apps_flagged": final_run.apps_flagged,
    }
