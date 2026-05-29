"""
Orchestrator — LangGraph state machine driving the full portal → job pipeline.

Flow:
  start → for each portal:
    search → dedup → score → for each top job:
      tailor → apply → record
  → complete
"""
import asyncio
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
import operator

from app.models.schemas import (
    JobListing, ParsedResume, UserProfile, UserPreferences,
    RunSession, ApplicationRecord, RunStatus, ApplicationStatus
)
from app.agents.search import PORTAL_MAP
from app.agents.scoring import score_and_rank
from app.agents.tailoring import tailor_for_job
from app.agents.application import apply_to_job
from app.services.llm import parse_resume
from app.services.email import send_captcha_alert, send_run_complete


# ── State ────────────────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    run: RunSession
    profile: UserProfile
    prefs: UserPreferences
    resume: ParsedResume
    portals: List[str]
    current_portal_index: int
    seen_dedup_keys: set
    all_applications: Annotated[List[ApplicationRecord], operator.add]
    resume_version: int
    progress_callback: Optional[object]  # async callable for SSE


# ── Nodes ────────────────────────────────────────────────────────────────────

async def node_search(state: PipelineState) -> dict:
    portal = state["portals"][state["current_portal_index"]]
    run = state["run"]
    run.current_portal = portal
    run.status = RunStatus.running

    search_fn = PORTAL_MAP.get(portal)
    if not search_fn:
        return {"run": run}

    print(f"[Orchestrator] Searching {portal}...")
    jobs = await search_fn(state["prefs"], state["seen_dedup_keys"], limit=40)
    run.jobs_found += len(jobs)

    if state.get("progress_callback"):
        await state["progress_callback"]({
            "event": "portal_searched",
            "portal": portal,
            "jobs_found": len(jobs),
            "total_found": run.jobs_found,
        })

    return {"run": run, "_portal_jobs": jobs}


async def node_score(state: PipelineState) -> dict:
    jobs: List[JobListing] = state.get("_portal_jobs", [])
    run = state["run"]

    scored = await score_and_rank(
        jobs,
        state["resume"],
        state["prefs"],
        threshold=0.55,
        top_n=state["prefs"].max_apps_per_day,
    )
    run.jobs_after_dedup = run.jobs_after_dedup + len(scored) if hasattr(run, 'jobs_after_dedup') else len(scored)

    if state.get("progress_callback"):
        await state["progress_callback"]({
            "event": "jobs_scored",
            "portal": state["portals"][state["current_portal_index"]],
            "top_jobs": len(scored),
        })

    return {"run": run, "_scored_jobs": scored}


async def node_apply_batch(state: PipelineState) -> dict:
    jobs: List[JobListing] = state.get("_scored_jobs", [])
    run = state["run"]
    new_records: List[ApplicationRecord] = []
    version = state["resume_version"]

    for job in jobs:
        run.current_job = f"{job.title} @ {job.company}"
        print(f"[Orchestrator] Applying: {job.title} at {job.company}")

        # Tailor
        tailored = await tailor_for_job(job, state["resume"], state["prefs"], run.id, version)
        version += 1

        # Apply
        record = await apply_to_job(tailored, state["profile"], run.id)
        new_records.append(record)

        if record.status == ApplicationStatus.submitted:
            run.apps_submitted += 1
        elif record.status == ApplicationStatus.flagged:
            run.apps_flagged += 1
            # Fire CAPTCHA alert email
            await asyncio.to_thread(
                send_captcha_alert,
                state["profile"].email,
                job.company,
                job.title,
                job.url,
            )
        else:
            run.apps_failed += 1

        if state.get("progress_callback"):
            await state["progress_callback"]({
                "event": "application",
                "company": job.company,
                "title": job.title,
                "status": record.status,
                "portal": job.source,
                "score": job.score,
                "resume_version": record.resume_version,
                "cover_letter_sent": record.cover_letter_sent,
                "message_sent": record.hiring_message_sent,
                "message_preview": record.hiring_message_preview,
            })

        # Respect daily cap
        if run.apps_submitted >= state["prefs"].max_apps_per_day:
            break

        await asyncio.sleep(3)  # polite delay between applications

    return {"run": run, "all_applications": new_records, "resume_version": version}


def node_next_portal(state: PipelineState) -> dict:
    return {"current_portal_index": state["current_portal_index"] + 1}


def node_complete(state: PipelineState) -> dict:
    run = state["run"]
    run.status = RunStatus.completed
    run.current_portal = None
    run.current_job = None
    return {"run": run}


# ── Routing ──────────────────────────────────────────────────────────────────

def route_portal(state: PipelineState) -> str:
    idx = state["current_portal_index"]
    portals = state["portals"]
    apps = state["run"].apps_submitted
    max_apps = state["prefs"].max_apps_per_day

    if apps >= max_apps:
        return "complete"
    if idx >= len(portals):
        return "complete"
    return "search"


# ── Build graph ──────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(PipelineState)
    g.add_node("search", node_search)
    g.add_node("score", node_score)
    g.add_node("apply_batch", node_apply_batch)
    g.add_node("next_portal", node_next_portal)
    g.add_node("complete", node_complete)

    g.set_entry_point("search")
    g.add_edge("search", "score")
    g.add_edge("score", "apply_batch")
    g.add_edge("apply_batch", "next_portal")
    g.add_conditional_edges("next_portal", route_portal, {"search": "search", "complete": "complete"})
    g.add_edge("complete", END)

    return g.compile()


# ── Entry point ──────────────────────────────────────────────────────────────

async def run_pipeline(
    run: RunSession,
    profile: UserProfile,
    prefs: UserPreferences,
    resume_text: str,
    progress_callback=None,
) -> tuple[RunSession, List[ApplicationRecord]]:
    """Run the full job application pipeline. Returns final run + all application records."""
    parsed = ParsedResume(raw_text=resume_text, **parse_resume(resume_text))

    initial_state: PipelineState = {
        "run": run,
        "profile": profile,
        "prefs": prefs,
        "resume": parsed,
        "portals": prefs.platforms,
        "current_portal_index": 0,
        "seen_dedup_keys": set(),
        "all_applications": [],
        "resume_version": 1,
        "progress_callback": progress_callback,
    }

    graph = build_graph()
    final_state = await graph.ainvoke(initial_state)

    final_run: RunSession = final_state["run"]
    applications: List[ApplicationRecord] = final_state["all_applications"]

    # Send completion email
    await asyncio.to_thread(
        send_run_complete,
        profile.email,
        {
            "apps_submitted": final_run.apps_submitted,
            "apps_flagged": final_run.apps_flagged,
        }
    )

    return final_run, applications
