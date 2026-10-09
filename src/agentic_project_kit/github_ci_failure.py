"""Observable CI failure policy; no clock, network or inferred test success."""
from __future__ import annotations

from agentic_project_kit.github_actions_run_checks import parse_github_datetime
from agentic_project_kit.github_check_policy import is_failed_check_conclusion

NOT_STARTED_MAX_SECONDS = 3


def classify_failed_job(job: dict) -> tuple[str, str]:
    if str(job.get("status", "")).lower() != "completed":
        return "PENDING", "job has not completed"
    if not is_failed_check_conclusion(str(job.get("conclusion", "")).upper()):
        return "UNKNOWN", "job is not a failed check"
    # A failed executable step overrides a short or missing timestamp.
    steps = job.get("steps")
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        return "UNKNOWN", "job step evidence is unavailable"
    if any(is_failed_check_conclusion(str(s.get("conclusion", "")).upper()) for s in steps):
        return "FAILED", "an executable job step failed"
    if "started_at" not in job:
        return "UNKNOWN", "start timestamp field is unavailable"
    start = job.get("started_at")
    if not start or str(start).startswith("0001-"):
        return "NOT_RUN", "job has no runner start timestamp"
    started = parse_github_datetime(start)
    ended = parse_github_datetime(job.get("completed_at"))
    if started is None or ended is None or ended < started:
        return "UNKNOWN", "job duration cannot be verified"
    duration = (ended - started).total_seconds()
    if duration <= NOT_STARTED_MAX_SECONDS:
        return "NOT_RUN", "failed within the documented 3-second startup boundary; no failed step"
    return "FAILED", "job ran longer than the startup boundary"
