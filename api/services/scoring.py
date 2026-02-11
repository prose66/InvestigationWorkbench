from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional


def score_event(
    event: dict,
    event_type_counts: Dict[str, int],
    last_seen: Optional[datetime],
    window_start: Optional[datetime],
) -> int:
    score = 0
    severity = (event.get("severity") or "").lower()
    outcome = (event.get("outcome") or "").lower()
    event_type = (event.get("event_type") or "").lower()

    if severity in ("high", "critical"):
        score += 2
    if "fail" in outcome or outcome in ("failure", "denied", "error"):
        score += 2
    if any(token in event_type for token in ("process", "privilege", "admin", "suspicious")):
        score += 2

    count = event_type_counts.get(event.get("event_type") or "", 0)
    if count and count <= 5:
        score += 1

    if last_seen and window_start and event.get("event_ts"):
        try:
            event_ts = datetime.fromisoformat(event["event_ts"].replace("Z", "+00:00"))
            total = (last_seen - window_start).total_seconds()
            if total > 0:
                threshold = window_start + timedelta(seconds=total * 0.9)
                if event_ts >= threshold:
                    score += 1
        except ValueError:
            pass

    return score
